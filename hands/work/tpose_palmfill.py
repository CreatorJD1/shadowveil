"""tpose: flat-skin fill in the palm (hidden at rest) for the small holes seen through the curled fist under the thumb."""
import json,numpy as np
from PIL import Image
from scipy import ndimage as ndi
import rigrender2 as R2
d='/workspace/shadowveil/hands/work/frames/tpose_v2'; rig=json.load(open(d+'/rig.json')); by={p['id']:p for p in rig['parts']}
blank='../../hands/work/_blank.png'
for side in 'LR':
    S=np.array(rig['hands'][side]['skinRGB']); pf=f"{d}/{by[side+'_palm']['file']}"; palm=np.array(Image.open(pf).convert('RGBA'))
    cover=np.zeros(palm.shape[:2],bool)   # opaque coverage by the other hand parts at rest
    acc=np.zeros(palm.shape[:2],np.uint8)
    for p in rig['parts']:
        if p['id'].startswith(side+'_') and p.get('file') and not p['id'].endswith('palm'):
            cover|=np.array(Image.open(f"{d}/{p['file']}").convert('RGBA'))[...,3]==255
    holes=np.zeros(palm.shape[:2],bool)
    for pose in ['Fist','Point','Peace']:
        for c in [0.5,0.62,0.75,0.87,1.0]:
            v={k:(x*c if k.startswith('Hand'+side) else 0) for k,x in R2.preset(pose).items()}
            im=R2.render('tpose',v,d,base=blank)[0]; a=np.array(im)[...,3]>100
            h=ndi.binary_fill_holes(a)&~a; holes|=ndi.binary_dilation(h,iterations=1)
    near=ndi.binary_dilation(palm[...,3]>=128,iterations=6)
    add=holes&cover&near&(palm[...,3]<255)
    palm[add,:3]=S; palm[add,3]=255; Image.fromarray(palm).save(pf); print(side,'palm fill px',int(add.sum()),'holes px',int(holes.sum()),'uncoverable',int((holes&~cover).sum()))
