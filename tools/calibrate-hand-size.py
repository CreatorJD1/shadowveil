"""Match reconstructed silhouettes to pinned turn references without stretching palms to wrist cuts."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
root=Path(__file__).resolve().parent.parent
folder=root/'rig/hand_angles'
refs=json.loads((root/'tools/hand-art/reference-size.json').read_text())
for name,ref in refs.items():
 path=folder/(name+'.json');j=json.loads(path.read_text())
 if j.get('sizeCalibration')==ref:continue
 a=np.array(Image.open(folder/(name+'.png')).convert('RGBA'))
 scale=j['textureScale'];origin=np.array(j['origin']);wp=np.array(j['wrist']);u=np.array([np.cos(j['axis']),np.sin(j['axis'])]);n=np.array([-u[1],u[0]])
 y,x=np.nonzero(a[:,:,3]>=240);opaque=np.stack([x,y],1)*scale+origin;rel=opaque-wp;along=rel@u;across=rel@n
 sl=j['physicalLength']/along.max();sw=ref['width']/np.ptp(across);ww=ref['wristWidth']/np.linalg.norm(np.diff(j['wristEdges'],axis=0));join=j['physicalLength']*.3/sl
 def width_at(t):
  blend=np.clip(1-t/join,0,1);blend=blend*blend*(3-2*blend)
  return sw+(ww-sw)*blend
 def warp(points):
  r=np.asarray(points)-wp;t=r@u;b=r@n
  return wp+np.expand_dims(t*sl,-1)*u+np.expand_dims(b*width_at(t),-1)*n
 moved=warp(opaque);lo=np.floor(moved.min(axis=0)/scale)*scale-2*scale;hi=np.ceil(moved.max(axis=0)/scale)*scale+3*scale
 size=np.ceil((hi-lo)/scale).astype(int);yy,xx=np.mgrid[:size[1],:size[0]];points=np.stack([xx,yy],-1)*scale+lo;r=points-wp;t=(r@u)/sl;b=(r@n)/width_at(t);old=wp+t[...,None]*u+b[...,None]*n;coords=((old-origin)/scale);sampling=[coords[:,:,1],coords[:,:,0]]
 tex=np.zeros((size[1],size[0],4),dtype=np.uint8)
 for c in range(4):tex[:,:,c]=map_coordinates(a[:,:,c],sampling,order=0 if c==3 else 1,mode='constant',cval=0)
 Image.fromarray(tex).save(folder/(name+'.png'))
 j['vertices']=warp(j['vertices']).tolist();j['wristEdges']=warp(j['wristEdges']).tolist()
 for p in j['parts']:
  p['pivotX'],p['pivotY']=warp([p['pivotX'],p['pivotY']]).tolist()
  if 'tip' in p:p['tip']=warp(p['tip']).tolist()
 j.update(origin=lo.tolist(),size=(size*scale).tolist(),sizeCalibration=ref)
 path.write_text(json.dumps(j,separators=(',',':')))
 print(name,'reference length/width',round(ref['length'],2),round(ref['width'],2))
