from pathlib import Path
import json,math
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
root=Path(__file__).resolve().parent.parent
out=root/'rig/hand_angles'
atlases={'L':root/'tools/hand-art/left-angles.png','R':root/'tools/hand-art/right-angles.png'}
# Landmarks on the restored atlas: wrist crease centre then anatomical fingertips.
marks={'L':[
([162,154],[[471,242],[520,523],[443,624],[356,640],[256,610]]),
([964,151],[[610,270],[620,530],[650,632],[723,624],[800,612]]),
([1402,164],[[1215,248],[1186,516],[1234,608],[1281,655],[1366,605]]),
([1687,167],[[1940,240],[1958,480],[1945,620],[1860,650],[1795,610]])],
'R':[
([420,174],[[151,251],[101,511],[146,602],[207,611],[297,596]]),
([632,169],[[812,248],[900,491],[848,601],[780,630],[679,597]]),
([1101,164],[[1490,249],[1466,492],[1432,612],[1367,640],[1291,640]]),
([1914,171],[[1700,268],[1655,540],[1725,650],[1816,640],[1870,600]])]}
F=['Thumb','Index','Middle','Ring','Pinky']
for side,path in atlases.items():
 a=np.array(Image.open(path).convert('RGBA'));mask=a[:,:,3]>=248;lab,n=ndi.label(mask);sizes=np.bincount(lab.ravel());ids=sorted(np.argsort(sizes[1:])[-4:]+1,key=lambda k:np.nonzero(lab==k)[1].mean())
 for z,(angle,k) in enumerate(zip([45,135,225,315],ids)):
  wpCut=np.array(marks[side][z][0],float);axisCut=np.array(marks[side][z][1][2],float)-wpCut;axisCut/=np.linalg.norm(axisCut);yy,xx=np.mgrid[:a.shape[0],:a.shape[1]];sel=(lab==k)&(((xx-wpCut[0])*axisCut[0]+(yy-wpCut[1])*axisCut[1])>=-1);ys,xs=np.nonzero(sel);x0,y0=xs.min()-2,ys.min()-2;x1,y1=xs.max()+3,ys.max()+3
  tex=a[y0:y1,x0:x1].copy();sub=sel[y0:y1,x0:x1];tex[:,:,3]=sub*255
  # Palette normalization for exported rig textures, retaining ink and shadows.
  luminance=tex[:,:,:3].mean(axis=2);skin=sub&(luminance>=125);shadow=sub&(luminance>=65)&(luminance<125);ink=sub&(luminance<65)
  tex[skin,:3]=[186,129,86];tex[shadow,:3]=[160,108,67];tex[ink,:3]=[36,29,26]
  Image.fromarray(tex).save(out/f'{angle}_{side}.png')
  j=json.loads((out/f'{angle}_{side}.json').read_text());oldwp=np.array(j['wrist']);wp=np.array(marks[side][z][0],float);tips=np.array(marks[side][z][1],float);u=tips[2]-wp;u/=np.linalg.norm(u);nvect=np.array([-u[1],u[0]])
  scale=j['physicalLength']/max(np.dot(tips-wp,u));origin=oldwp+(np.array([x0,y0])-wp)*scale
  conv=lambda p:(oldwp+(np.array(p)-wp)*scale)
  parts=[dict(id=side+'_palm',file=f'{angle}_{side}.png',pivotX=float(oldwp[0]),pivotY=float(oldwp[1]),parent=None,layer=320,maxCurlDeg=0)];chains=[]
  for fi,f in enumerate(F):
   base=wp+(tips[fi]-wp)*(.38 if fi==0 else .62);chain=np.array([base+(tips[fi]-base)*t for t in [0,.47,.76,1]]);chains.append(chain)
   for b in range(3):
    p=conv(chain[b]);parts.append(dict(id=f'{side}_{f}{b+1}',file=f'{angle}_{side}.png',pivotX=round(float(p[0]),4),pivotY=round(float(p[1]),4),tip=conv(chain[b+1]).tolist(),parent=side+'_palm' if b==0 else f'{side}_{f}{b}',layer=321+fi*3+b,maxCurlDeg=(1 if side=='L' else -1)*[12,8,6][b]))
  gy=list(range(y0,y1,10))+[y1-1];gx=list(range(x0,x1,10))+[x1-1];gx=sorted(set(gx));gy=sorted(set(gy));verts=[];weights=[]
  for y in gy:
   for x in gx:
    q=np.array([x,y]);verts.append(conv(q).tolist());dist=[]
    for c in chains:
     d=c[-1]-c[0];t=np.clip((q-c[0])@d/(d@d),0,1);dist.append(np.linalg.norm(q-c[0]-t*d))
    fi=int(np.argmin(dist));c=chains[fi];d=c[-1]-c[0];t=np.clip((q-c[0])@d/(d@d),0,1)
    # Palm owns the proximal region; cross-joint blending keeps the mesh continuous.
    along=np.dot(q-wp,u);baseAlong=np.dot(c[0]-wp,u);blend=np.clip((along-baseAlong+8)/16,0,1)
    joint=0 if t<.47 else 1 if t<.76 else 2;bone=1+fi*3+joint;w=[[bone,1.]]
    for b in [1,2]:
     pivot=[0,.47,.76][b]
     if abs(t-pivot)<.09:
      f=(t-pivot+.09)/.18;w=[[1+fi*3+b-1,1-f],[1+fi*3+b,f]];break
    if blend<1:w=[[0,1-blend]]+[[b,v*blend] for b,v in w]
    weights.append([[int(b),float(v)] for b,v in w if v>1e-8])
  tri=[];nx=len(gx)
  for y in range(len(gy)-1):
   for x in range(nx-1):
    if sub[max(0,gy[y]-y0-10):min(sub.shape[0],gy[y+1]-y0+11),max(0,gx[x]-x0-10):min(sub.shape[1],gx[x+1]-x0+11)].any():
     b=y*nx+x;tri.extend([[b,b+1,b+nx],[b+1,b+nx+1,b+nx]])
  # Wrist span is measured on the clean cutout at the authored wrist plane.
  rel=np.stack([xs,ys],1)-wp;cross=rel@nvect;along=rel@u;section=cross[np.abs(along)<3];half=(np.ptp(section)/2 if len(section)>2 else 65)*scale
  j.pop('sizeCalibration',None)
  j.update(origin=origin.tolist(),size=[(x1-x0)*scale,(y1-y0)*scale],textureScale=scale,wrist=oldwp.tolist(),axis=math.atan2(u[1],u[0]),wristEdges=[(oldwp+nvect*(float(section.min())*scale if len(section)>2 else -half)).tolist(),(oldwp+nvect*(float(section.max())*scale if len(section)>2 else half)).tolist()],parts=parts,vertices=verts,weights=weights,triangles=tri,quality='Reconstructed high resolution artwork, palette matched to base model',atlasSource=Path(path).name)
  (out/f'{angle}_{side}.json').write_text(json.dumps(j,separators=(',',':')))
  print(angle,side,tex.shape[1],tex.shape[0])

# Preserve the reference silhouette size and foreshortening after reconstruction.
import runpy
runpy.run_path(str(root/'tools/calibrate-hand-size.py'))
