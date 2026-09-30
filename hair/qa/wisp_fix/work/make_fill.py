# Wisp underfill for tpose hair_back.png: wisp mask dilated 3 px (disk), colours sampled from base.png
# (non-wisp pixels: base.png as-is; wisp pixels (drawn hair in base): nearest non-wisp base.png pixel inside the fill).
# Kept only where the rest stack above hair_back (skin/body, eyes, mouth, hands, other hair) is alpha 255 -> hidden at rest.
import numpy as np, json, glob, sys
from PIL import Image
from scipy import ndimage as ndi
R='/workspace/shadowveil'; V=R+'/views/tpose'
def A(p): return np.array(Image.open(p).convert('RGBA'))
base=A(V+'/base.png'); hb=A(R+'/hair/backups/wisp_fix_20260930/tpose_hair_back.png')
w=np.array(Image.open(R+'/hair/tpose_eye_crossing_wisp_mask.png').convert('L'))>127
yy,xx=np.mgrid[-3:4,-3:4]; disk=(xx**2+yy**2)<=9+1   # radius ~3
F=ndi.binary_dilation(w,structure=disk)
# rest alpha of everything drawn above hair_back (layer>100): the rest composite equals base.png (0 px), so its alpha is base alpha;
# additionally require the actual above-stack alpha from the rest_check composite without hair_back
above=np.array(Image.open(R+'/hair/qa/wisp_fix/work/rest_above_alpha_tpose.png'))
keep=F&(above==255)&(hb[...,3]==0)
src=~w
idx=ndi.distance_transform_edt(~src,return_distances=False,return_indices=True)
col=base[idx[0],idx[1],:3]
out=hb.copy(); out[keep,:3]=col[keep]; out[keep,3]=255
Image.fromarray(out).save(V+'/hair/hair_back.png')
Image.fromarray((keep*255).astype(np.uint8)).save(R+'/hair/qa/wisp_fix/work/fill_mask_tpose.png')
cols={}
for c in map(tuple,out[keep,:3]): cols[str(c)]=cols.get(str(c),0)+1
print('dilated',int(F.sum()),'kept',int(keep.sum()),'dropped(not hidden)',int((F&~keep).sum()),'wisp px',int(w.sum()))
print('colours',sorted(cols.items(),key=lambda k:-k[1]))
r,g,b=[out[...,i].astype(int) for i in range(3)]; a=out[...,3]
print('chroma',int(((a>0)&(b>r+40)&(b>g+40)).sum()),'white',int(((a>0)&(r>240)&(g>240)&(b>240)).sum()))
