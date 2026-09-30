# Builds views/<view>/base_body.png = base.png with exactly the owners' erase masks cleared (no widening).
# Outside the masks every pixel equals base.png. Inside: transparent, except flat skin fill where body continues underneath.
import sys
from PIL import Image; import numpy as np
from scipy import ndimage
def load(p):
  m=np.array(Image.open(p)); return (m[...,-1] if m.ndim==3 else m)>127
for v in (sys.argv[1:] or ['apose','tpose','left','right','back']):   # optional: only the given views
  b=np.array(Image.open(f'views/{v}/base.png')).astype(np.int32)
  hand=load(f'hands/{v}_hand_erase_mask.png'); hair=load(f'hair/{v}_hair_erase_mask.png')
  allm=hand|hair; out=b.copy(); out[allm]=0
  skin=~allm&(b[...,3]==255)&(b[...,0]>140)&(b[...,2]<120)&(b[...,0]-b[...,2]>60)
  si=ndimage.distance_transform_edt(~skin,return_distances=False,return_indices=True)
  sm=np.round(ndimage.uniform_filter(b[si[0],si[1]][...,:3].astype(float),size=(15,15,1))).astype(int)
  fill=np.zeros_like(allm)
  if v in ('left','right'):  # thigh under hand
    al=(b[...,3]>200)&~allm; ys,xs=np.nonzero(hand); y0,y1=ys.min()-3,ys.max()+3; x0,x1=xs.min(),xs.max()
    def span(y):
      lab,k=ndimage.label(al[y]); c=[np.nonzero(lab==i)[0] for i in range(1,k+1)]
      c=[xx for xx in c if xx.max()>=x0-5 and xx.min()<=x1+5]; xx=np.concatenate(c); return xx.min(),xx.max()
    top,bot=span(y0),span(y1)
    for y in range(y0,y1+1):
      t=(y-y0)/max(1,y1-y0); L=int(round(top[0]*(1-t)+bot[0]*t)); R=int(round(top[1]*(1-t)+bot[1]*t))
      for x in range(L,R+1):
        if hand[y,x]:
          if x-L<2 or R-x<2: out[y,x]=[40,32,30,255]
          else: fill[y,x]=True
  op=ndimage.uniform_filter((~allm).astype(float),25); sk=ndimage.uniform_filter(skin.astype(float),25)
  fill|=hair&(np.where(op>0,sk/np.maximum(op,1e-6),0)>0.5)
  out[fill,:3]=sm[fill]; out[fill,3]=255
  # ear/jaw outline under hair strands (body_tools/ear_line_fill.json): flat line colour, only inside the hair erase mask
  import json,os
  ef=os.path.join(os.path.dirname(os.path.abspath(__file__)),'ear_line_fill.json'); nline=0
  if os.path.exists(ef):
    E=json.load(open(ef))
    for x,y in E.get(v,[]):
      assert hair[y,x], f'{v}: ear line px {(x,y)} outside hair erase mask'
      out[y,x,:3]=E['rgb']; out[y,x,3]=255; nline+=1
  import os; _t=f'views/{v}/base_body.png.tmp'; Image.fromarray(out.astype(np.uint8),'RGBA').save(_t,format='PNG'); os.replace(_t,f'views/{v}/base_body.png')  # atomic
  diff=((out!=b).any(-1)&~allm).sum()
  print(v,'masked',int(allm.sum()),'filled',int(fill.sum()),'ear line',nline,'changed outside masks',int(diff))
