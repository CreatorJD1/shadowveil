# silhouette at theta+180 = mirror of silhouette at theta (orthographic) -> check 135 vs mirror(f191), 225 vs mirror(f033), and vice versa
import sys, json, numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0,'/workspace/shadowveil/body_tools/work/apose_turn'); from seg import mask_of
FR='/workspace/shadowveil/reference/apose_turn/frames/f%03d.png'
def norm(f,mirror=False):
    m=mask_of(FR%f); ys,xs=np.nonzero(m); t,b=ys.min(),ys.max(); s=1000/(b-t)
    hb=m[int(t+.45*(b-t)):int(t+.5*(b-t))]; cx=np.median(np.nonzero(hb)[1])
    if mirror: m=m[:,::-1]; cx=m.shape[1]-1-cx
    im=Image.fromarray((m*255).astype(np.uint8)).transform((800,1100),Image.AFFINE,(1/s,0,cx-400/s,0,1/s,t-50/s),resample=Image.BILINEAR)
    return np.array(im)>127
def iou(a,b): return round(float((a&b).sum()/(a|b).sum()),4)
def edge_metrics(f):
    g=np.array(Image.open(FR%f).convert('L')).astype(float); m=mask_of(FR%f)
    gm=np.hypot(nd.sobel(g,0),nd.sobel(g,1)); inner=nd.binary_erosion(m,iterations=3)
    edge=nd.binary_dilation(m,iterations=1)^nd.binary_erosion(m,iterations=1)
    return round(float(np.percentile(gm[inner],99)),1), round(float(gm[edge].mean()),1)
def motion(f):
    a=lambda k: np.array(Image.open(FR%k).convert('L')).astype(float)
    return round(float((np.abs(a(f)-a(f-1)).mean()+np.abs(a(f+1)-a(f)).mean())/2),2)
out={}
refs={45:33,315:191}
M33=norm(33,True); M191=norm(191,True)
for ang,c,ref in ((45,33,None),(315,191,None),(135,87,M191),(225,131,M33)):
    for f in range(c-4,c+5):
        d={'inner_grad_p99':edge_metrics(f)[0],'edge_grad_mean':edge_metrics(f)[1],'motion_meanabs':motion(f)}
        if ref is not None: d['iou_vs_mirror_of_'+('f191' if ang==135 else 'f033')]=iou(norm(f),ref)
        out.setdefault(str(ang),{})[f]=d
# reverse check: which 45/315 frame best mirrors the chosen 135/225 candidates
for ang,c,back in ((45,33,132),(45,33,131),(315,191,87)):
    R=norm(back,True)
    for f in range(c-4,c+5): out[str(ang)][f]['iou_vs_mirror_of_f%03d'%back]=iou(norm(f),R)
json.dump(out,open('/workspace/shadowveil/body_tools/work/apose_turn/diagonals/_mirror_sharp.json','w'),indent=1)
for a,v in out.items():
    print('==',a)
    for f,d in v.items(): print(f,d)
