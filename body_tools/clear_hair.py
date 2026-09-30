# Clears hair-mask areas from views/<view>/base_body.png (run after hand clearing).
# Pixels under strands that sit over skin get a blended skin fill; the rest go transparent (hair_back covers them).
from PIL import Image; import numpy as np, sys
from scipy import ndimage
R=int(sys.argv[1]) if len(sys.argv)>1 else 3
for v in ['apose','tpose','left','right','back']:
  b=np.array(Image.open(f'views/{v}/base.png')).astype(np.int32)
  cur=np.array(Image.open(f'views/{v}/base_body.png')).astype(np.int32)
  hm=np.array(Image.open(f'hair/{v}_hair_erase_mask.png')); hm=(hm[...,-1] if hm.ndim==3 else hm)>127
  hm=ndimage.binary_dilation(hm,iterations=R)
  outside=~hm
  skin=outside&(b[...,3]==255)&(b[...,0]>140)&(b[...,2]<120)&(b[...,0]-b[...,2]>60)
  sk=ndimage.uniform_filter(skin.astype(float),25); op=ndimage.uniform_filter(outside.astype(float),25)
  fillm=hm&(np.where(op>0,sk/np.maximum(op,1e-6),0)>0.5)
  si=ndimage.distance_transform_edt(~skin,return_distances=False,return_indices=True)
  sm=ndimage.uniform_filter(b[si[0],si[1]][...,:3].astype(float),size=(15,15,1))
  out=cur.copy(); out[hm]=0
  out[fillm,:3]=np.round(sm[fillm]).astype(int); out[fillm,3]=255
  Image.fromarray(out.astype(np.uint8),'RGBA').save(f'views/{v}/base_body.png')
  bg=Image.new('RGBA',(1365,1739),(0,0,255,255)); bg.alpha_composite(Image.fromarray(out.astype(np.uint8),'RGBA'))
  ys,xs=np.nonzero(hm); bg.crop((max(0,xs.min()-30),max(0,ys.min()-30),xs.max()+30,ys.max()+30)).save(f'views/{v}/base_body_preview_head.png')
  print(v,int(hm.sum()),int(fillm.sum()))
