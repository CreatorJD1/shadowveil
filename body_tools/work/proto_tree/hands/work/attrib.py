import json,sys,numpy as np
from PIL import Image
import rigrender2 as R2
from collections import Counter
V,d,pose,c,side=sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4]),sys.argv[5]; x0,y0,x1,y1=map(int,sys.argv[6:10])
v={k:x*c for k,x in R2.preset(pose).items()}; rig=json.load(open(d+'/rig.json')); M,PV,CP=R2.chain(rig,v)
lab=np.full((1739,1365),'',dtype=object); dark=np.zeros((1739,1365),bool)
for p in sorted(rig['parts'],key=lambda p:p['layer']):
  if not p.get('file') or not p['id'].startswith(side+'_'): continue
  e=R2.fsel(v,p); im=Image.open(d+'/'+(e['file'] if e else p['file'])).convert('RGBA')
  inv=np.linalg.inv(M[p['id']]); t=np.array(im.transform((1365,1739),Image.AFFINE,tuple(inv[0])+tuple(inv[1]),resample=Image.NEAREST))
  m=t[...,3]>128; lab[m]=p['id']; dark[m]=t[m][:,:3].sum(1)<250
print(Counter(lab[y,x] for y in range(y0,y1) for x in range(x0,x1) if dark[y,x]))
