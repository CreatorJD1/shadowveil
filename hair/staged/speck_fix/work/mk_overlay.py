# Scratch overlay of the project for simulation (never writes to the live tree).
#   python3 mk_overlay.py <overlay_dir> <scenario>
# scenario: live            = live files only (baseline)
#           staged          = staged strands + staged erase masks + staged validator, CURRENT (not rebuilt) base_body/skin
#           staged_rebuilt  = staged + scratch base_body.png/base_body_skin.png with the speck px cleared (alpha 0),
#                             i.e. what Base Body's rebuild should produce at those px
#           live_clearhair  = control: live hair/mask, body images run through the same clear_hair.py copy
#           staged_clearhair= staged + scratch body images run through a copy of the clear_hair.py logic (R=3, skin fill)
#                             with the staged mask, applied to the current base_body.png and base_body_skin.png
import os, sys, shutil, json, numpy as np
from PIL import Image
from scipy import ndimage
R='/workspace/shadowveil'; ST=R+'/hair/staged/speck_fix'; O=os.path.abspath(sys.argv[1]); SC=sys.argv[2]
V=['apose','tpose','left','right','back']
assert not O.startswith(R+'/')
shutil.rmtree(O,ignore_errors=True); os.makedirs(O)
def linkdir(src,dst,real_children=()):
    os.makedirs(dst,exist_ok=True)
    for n in os.listdir(src):
        if n in real_children: continue
        os.symlink(os.path.join(src,n),os.path.join(dst,n))
for n in os.listdir(R):
    if n not in ('views','hair','rig'): os.symlink(f'{R}/{n}',f'{O}/{n}')
linkdir(f'{R}/views',f'{O}/views',V)
for v in V:
    linkdir(f'{R}/views/{v}',f'{O}/views/{v}',('hair','base_body.png','base_body_skin.png'))
    linkdir(f'{R}/views/{v}/hair',f'{O}/views/{v}/hair')
    for f in ('base_body.png','base_body_skin.png'): shutil.copy2(f'{R}/views/{v}/{f}',f'{O}/views/{v}/{f}')
linkdir(f'{R}/hair',f'{O}/hair',('validation.json','validate_hair.py')+tuple(f'{v}_hair_erase_mask.png' for v in V))
linkdir(f'{R}/rig',f'{O}/rig',tuple(f'rest_diff_{v}.png' for v in V)+('rest_check.py',))
shutil.copy2(f'{R}/rig/rest_check.py',f'{O}/rig/rest_check.py')
val=f'{ST}/validate_hair.py' if SC not in ('live','live_clearhair') else f'{R}/hair/validate_hair.py'
s=open(val).read(); assert s.count("R='/workspace/shadowveil'")==1
open(f'{O}/hair/validate_hair.py','w').write(s.replace("R='/workspace/shadowveil'",f"R='{O}'"))
for v in V: shutil.copy2(f'{R}/hair/{v}_hair_erase_mask.png',f'{O}/hair/{v}_hair_erase_mask.png')
if SC not in ('live','live_clearhair'):
    for root,_,fs in os.walk(ST+'/views'):
        for f in fs:
            rel=os.path.relpath(os.path.join(root,f),ST); d=f'{O}/{rel}'
            os.remove(d); shutil.copy2(f'{ST}/{rel}',d)
    for v in V: shutil.copy2(f'{ST}/hair/{v}_hair_erase_mask.png',f'{O}/hair/{v}_hair_erase_mask.png')
if SC=='staged_rebuilt':
    for v in V:
        add=np.array(Image.open(f'{ST}/for_base_body/{v}_speck_px_ADD.png'))>127
        for f in ('base_body.png','base_body_skin.png'):
            p=f'{O}/views/{v}/{f}'; a=np.array(Image.open(p).convert('RGBA')); a[add]=0; Image.fromarray(a,'RGBA').save(p)
if SC in ('staged_clearhair','live_clearhair'):
    for v in V:
        b=np.array(Image.open(f'{R}/views/{v}/base.png')).astype(np.int32)
        hm=np.array(Image.open(f'{O}/hair/{v}_hair_erase_mask.png')); hm=(hm[...,-1] if hm.ndim==3 else hm)>127
        hm=ndimage.binary_dilation(hm,iterations=3); outside=~hm
        skin=outside&(b[...,3]==255)&(b[...,0]>140)&(b[...,2]<120)&(b[...,0]-b[...,2]>60)
        sk=ndimage.uniform_filter(skin.astype(float),25); op=ndimage.uniform_filter(outside.astype(float),25)
        fillm=hm&(np.where(op>0,sk/np.maximum(op,1e-6),0)>0.5)
        si=ndimage.distance_transform_edt(~skin,return_distances=False,return_indices=True)
        sm=ndimage.uniform_filter(b[si[0],si[1]][...,:3].astype(float),size=(15,15,1))
        for f in ('base_body.png','base_body_skin.png'):
            p=f'{O}/views/{v}/{f}'; cur=np.array(Image.open(p).convert('RGBA')).astype(np.int32)
            out=cur.copy(); out[hm]=0; out[fillm,:3]=np.round(sm[fillm]).astype(int); out[fillm,3]=255
            Image.fromarray(out.astype(np.uint8),'RGBA').save(p)
print('overlay',O,SC)
