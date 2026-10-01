from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
class MCP_Geometric:
 def __init__(self,cost):
  self.shape=cost.shape;h,w=self.shape;ids=np.arange(h*w).reshape(h,w);a=[];b=[];v=[]
  for dy,dx in [(0,1),(1,0),(1,1),(1,-1)]:
   ya,yb=(slice(0,h-dy),slice(dy,h));xa,xb=(slice(0,w-dx),slice(dx,w)) if dx>=0 else (slice(-dx,w),slice(0,w+dx))
   aa=ids[ya,xa].ravel();bb=ids[yb,xb].ravel();vv=(cost[ya,xa].ravel()+cost[yb,xb].ravel())*.5*math.hypot(dx,dy)
   a.extend([aa,bb]);b.extend([bb,aa]);v.extend([vv,vv])
  self.graph=coo_matrix((np.concatenate(v),(np.concatenate(a),np.concatenate(b))),shape=(h*w,h*w)).tocsr()
 def find_costs(self,seeds):
  indices=[y*self.shape[1]+x for y,x in seeds];return dijkstra(self.graph,indices=indices,min_only=True).reshape(self.shape),None
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'hands/work/turn_check'))
def fg(im):
 im=im.astype(int);return ~((im[:,:,2]>120)&(im[:,:,2]>im[:,:,0]+60)&(im[:,:,2]>im[:,:,1]+60))
from arm2 import arms2,wrist2,geoball
sys.path.insert(0,str(root/'hands/work'))
from defs import D
out=root/'rig/hand_angles'
records=json.load(open(root/'hands/work/turn_check/sweep2.json'))
sil=json.load(open(root/'hands/work/turn_check/silhouette.json'))
# Tips are annotated on the original frames; fingers that overlap still receive
# independent chains, without painting hidden surfaces into the reference art.
tips={
'f035':{'R':[[175,495],[173,537],[178,551],[185,552],[194,550]],'L':[[638,512],[651,559],[641,575],[627,577],[609,575]]},
'f086':{'R':[[582,501],[591,539],[585,553],[576,555],[565,553]],'L':[[110,517],[110,567],[114,581],[128,578],[143,572]]},
'f133':{'R':[[647,513],[653,561],[645,577],[633,579],[615,577]],'L':[[181,503],[172,543],[178,555],[186,557],[198,555]]},
'f189':{'R':[[127,514],[116,563],[126,579],[138,581],[156,577]],'L':[[590,503],[591,539],[587,553],[578,555],[568,554]]}}
names=['Thumb','Index','Middle','Ring','Pinky'];manifest=[]
for frame,angle in [('f035',45),('f086',135),('f133',225),('f189',315)]:
 idx=int(frame[1:])-1;rec=records[idx];img=np.array(Image.open(root/'reference/apose_turn/frames'/f'{frame}.png').convert('RGB'));m=fg(img)
 comps=[]
 for fr in (.30,.40,.50):
  for c in arms2(m,sil[idx]['top'],rec['H'],fr):
   if all(np.linalg.norm(np.array(c['tip'])-q['tip'])>15 for q in comps):comps.append(c)
 for side in ['L','R']:
  h=rec['hands'][side];wp=np.array(h['wrist']);u=np.array(h['axis']);n=np.array([-u[1],u[0]])
  # Select the matching isolated arm and cut at the measured wrist crease.
  c=min(comps,key=lambda c:np.linalg.norm(np.array(c['tip'])-np.mean(tips[frame][side][1:],axis=0)))
  gb=geoball(m,c['tip'],int(170*rec['H']/1056));yy,xx=np.mgrid[:m.shape[0],:m.shape[1]]
  mask=gb&(((xx-wp[0])*u[0]+(yy-wp[1])*u[1])>=-1)
  ys,xs=np.nonzero(mask);x0,y0=int(xs.min())-3,int(ys.min())-3;x1,y1=int(xs.max())+4,int(ys.max())+4
  rgba=np.zeros((y1-y0,x1-x0,4),np.uint8);rgba[:,:,:3]=img[y0:y1,x0:x1];rgba[:,:,3]=mask[y0:y1,x0:x1]*255
  # Remove chroma spill by sampling the closest existing non-blue art pixel.
  # Geometry/opacity remain unchanged; no new skin or outline colour is painted.
  rgb=rgba[:,:,:3].astype(int);opaque=mask[y0:y1,x0:x1];clean=opaque&(rgb[:,:,2]<=np.maximum(rgb[:,:,0],rgb[:,:,1])+10)
  nearestRGB=ndi.distance_transform_edt(~clean,return_distances=False,return_indices=True);spill=opaque&~clean;rgba[spill,:3]=rgba[nearestRGB[0][spill],nearestRGB[1][spill],:3]
  fname=f'{angle}_{side}.png';Image.fromarray(rgba).save(out/fname)
  donor='apose' if angle in [45,315] else 'back';defs=D[donor][side];w0=np.mean(defs['wrist'],axis=0);ch0=np.array(defs['fingers']['middle']);oldU=ch0[-1]-w0;oldU/=np.linalg.norm(oldU);oldN=np.array([-oldU[1],oldU[0]])
  baseDist=float((ch0[0]-w0)@oldU);widthScale=h['palm_w']/(60 if donor=='apose' else 58);lengthScale=h['palm_len']/baseDist
  chains={};parts=[dict(id=side+'_palm',file=fname,pivotX=float(wp[0]),pivotY=float(wp[1]),parent=None,layer=320,maxCurlDeg=0)]
  for fi,f in enumerate(names):
   base0=np.array(defs['fingers'][f.lower()][0]);d=base0-w0;base=wp+u*(d@oldU)*lengthScale+n*(d@oldN)*widthScale;tip=np.array(tips[frame][side][fi],float)
   # Snap base onto the closest actual hand pixel, keeping annotations on art.
   near=np.argmin((xs-base[0])**2+(ys-base[1])**2);base=np.array([xs[near],ys[near]],float)
   chain=[base+(tip-base)*t for t in [0,.47,.76,1]];chains[f]=chain
   for k in range(3):
    a=chain[k];parts.append(dict(id=f'{side}_{f}{k+1}',file=fname,pivotX=round(a[0],4),pivotY=round(a[1],4),tip=chain[k+1].tolist(),parent=side+'_palm' if k==0 else f'{side}_{f}{k}',layer=321+fi*3+k,maxCurlDeg=(1 if side=='L' else -1)*[12,8,6][k]))
  # Geodesic regions follow the actual ink-separated finger silhouettes.
  submask=mask[y0:y1,x0:x1];cost=np.where(submask,1.,1e7);dark=rgba[:,:,:3].mean(axis=2)<75;cost[dark&submask]=8
  seeds=[]
  seedPalm=[]
  for t in np.linspace(.05,.42,12):seedPalm.append((wp+u*h['palm_len']*t-np.array([x0,y0]))[::-1])
  seeds.append(seedPalm)
  for f in names:
   c=chains[f];seeds.append([(c[0]+(c[-1]-c[0])*t-np.array([x0,y0]))[::-1] for t in np.linspace(.03,.98,18)])
  distances=[]
  for seed in seeds:
   st=[]
   for y,x in seed:
    y,x=int(round(y)),int(round(x))
    if 0<=y<submask.shape[0] and 0<=x<submask.shape[1] and submask[y,x]:st.append((y,x))
   if st:distances.append(MCP_Geometric(cost).find_costs(st)[0])
   else:distances.append(np.full(submask.shape,1e9))
  labels=np.argmin(np.stack(distances),axis=0);nearest=ndi.distance_transform_edt(~submask,return_distances=False,return_indices=True)
  labels=labels[nearest[0],nearest[1]]
  gx=list(range(x0,x1,2));gy=list(range(y0,y1,2));gx.append(x1-1);gy.append(y1-1);gx=sorted(set(gx));gy=sorted(set(gy));vertices=[];weights=[]
  for y in gy:
   for x in gx:
    vertices.append([x,y]);lab=int(labels[y-y0,x-x0]);q=np.array([x,y],float)
    if lab==0:weights.append([[0,1.]])
    else:
     ch=chains[names[lab-1]];proj=np.clip(((q-ch[0])@(ch[-1]-ch[0]))/(np.linalg.norm(ch[-1]-ch[0])**2+1e-8),0,1);knots=[0,.47,.76,1];joint=0 if proj<.47 else 1 if proj<.76 else 2
     bone=1+(lab-1)*3+joint
     # Blend across attachment and joint bands; connected triangles retain ink.
     band=.08;wgt=[[bone,1.]]
     if proj<band:wgt=[[0,1-proj/band],[1+(lab-1)*3,proj/band]]
     else:
      for j in [1,2]:
       if abs(proj-knots[j])<band:
        a=(proj-knots[j]+band)/(2*band);wgt=[[1+(lab-1)*3+j-1,1-a],[1+(lab-1)*3+j,a]];break
     weights.append([[b,round(w,6)] for b,w in wgt if w>0])
  triangles=[];nx=len(gx)
  for j in range(len(gy)-1):
   for i in range(nx-1):
    if submask[max(0,gy[j]-y0-2):min(submask.shape[0],gy[j+1]-y0+3),max(0,gx[i]-x0-2):min(submask.shape[1],gx[i+1]-x0+3)].any():
     a=j*nx+i;triangles.extend([[a,a+1,a+nx],[a+1,a+nx+1,a+nx]])
  meta=dict(angle=angle,side=side,source=f'reference/apose_turn/frames/{frame}.png',image=fname,origin=[x0,y0],size=[x1-x0,y1-y0],wrist=wp.tolist(),axis=math.atan2(u[1],u[0]),wristEdges=[(wp-n*h['wrist_w']/2).tolist(),(wp+n*h['wrist_w']/2).tolist()],physicalLength=93*rec['H']/1056,parts=parts,vertices=vertices,triangles=triangles,weights=weights,spread={f'Hand{side}Spread':{'fingers':{f:{'maxSpreadDeg':(fi-2)*2} for fi,f in enumerate(names) if f!='Thumb'}},f'Hand{side}ThumbSpread':{'degAtPlus1':8,'degAtMinus1':-8}})
  jsonfile=f'{angle}_{side}.json';(out/jsonfile).write_text(json.dumps(meta,separators=(',',':')));manifest.append(dict(angle=angle,side=side,file=jsonfile))
(out/'manifest.json').write_text(json.dumps(manifest))
print('Created',len(manifest),'hand meshes; bytes',sum(p.stat().st_size for p in out.iterdir()))
