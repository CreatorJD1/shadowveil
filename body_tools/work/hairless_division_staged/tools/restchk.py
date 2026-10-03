import sys,json,numpy as np
sys.path.insert(0,'/workspace/tmpsv/hg'); from sim import load,comp
from PIL import Image
T='/workspace/shadowveil/body_tools/work/hairless_division_staged'; R='/workspace/shadowveil'
v=sys.argv[1]
def m(p):
    a=np.array(Image.open(p)); return (a[...,-1] if a.ndim==3 else a)>127
o,P=load(v,'pieces'); o2,Q=load(v,'pieces_pre_headgroup')
c=np.round(comp(o,P,0,0)).astype(int); c0=np.round(comp(o2,Q,0,0)).astype(int)
h=np.array(Image.open(f'{T}/{v}/hairless_{v}.png')).astype(int); h[h[...,3]==0]=0; c[c[...,3]==0]=0; c0[c0[...,3]==0]=0
hand=m(f'{T}/{v}/hand_mask.png')
d=(c!=h).any(-1)&~hand; d0=(c!=c0).any(-1)
nk=(np.array(Image.open(f'{T}/{v}/pieces/neck.png'))!=np.array(Image.open(f'{T}/{v}/pieces_pre_headgroup/neck.png'))).any(-1)
L={}
for k,p in [('eye',f'{R}/eyes/handoff_hairless/{v}_eye_brow_lock.png'),('mouth',f'{R}/mouth/handoff_hairless/{v}_mouth_lock.png'),('hand',f'{R}/hands/{v}_hand_erase_mask.png')]:
    try: L[k]=int((m(p)&d0).sum())
    except FileNotFoundError: pass
print(json.dumps({'view':v,'rebuild_diff_vs_hairless_outside_hand':int(d.sum()),'rest_diff_vs_previous_pieces':int(d0.sum()),'neck_px_changed':int(nk.sum()),'locks_changed_at_rest':L}))
