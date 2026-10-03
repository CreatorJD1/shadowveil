import numpy as np, json
from PIL import Image
from scipy.ndimage import shift as nshift, binary_dilation
from fitlib import *
R='/workspace/shadowveil/'
res={}
for run in ['normal_anger_apose','stress_anger_apose','normal_anger_tpose','stress_anger_tpose']:
  view=run.split('_')[-1]; W=R+f'rig/previews/actions/v1/work/{run}/'
  B=np.asarray(Image.open(R+f'views/{view}/base.png').convert('RGBA')).astype(float)/255
  A=np.asarray(Image.open(R+f'views/{view}/mouth/anger.png').convert('RGBA')).astype(float)/255
  RS=np.asarray(Image.open(R+f'views/{view}/mouth/rest.png').convert('RGBA')).astype(float)/255
  base=white(B); tA=white(comp(B,A))
  m=json.load(open(W+'meta.json')); fr=m['frames']
  ab=json.load(open(R+f'views/{view}/mouth/rig.json'))['partsBBox']['anger']; box=(ab[0]-4,ab[1]-4,ab[2]+5,ab[3]+5)
  rows=[]
  for i in [3,5,8,9,10,11,15,30,60,89]:
    p=W+f'frames/f{i:04d}.png'; raw=np.asarray(Image.open(p).convert('RGBA')).astype(int); img=load(p)
    ra=fit(img,tA,box); rr=fit(img,base,box)
    x0,y0,x1,y1=box;q=raw[y0:y1,x0:x1]; blue=int(np.sum((q[...,2]>np.maximum(q[...,0],q[...,1])+20)&(q[...,3]>0)))
    rows.append(dict(f=i,t=round(fr[i]['t'],4),pick=fr[i]['mouth'],talk=fr[i]['extra']['mouthTalk'],RootY=fr[i]['params']['RootY'],fit_anger=ra,fit_rest=rr,blue=blue))
  # fade frame 9: alpha of incoming anger at the f10 shift
  _,dx,dy=rows[[r['f'] for r in rows].index(10)]['fit_anger']
  img=load(W+'frames/f0009.png'); x0,y0,x1,y1=box; pad=5
  def sh(T): return nshift(T[y0-pad:y1+pad,x0-pad:x1+pad],(dy,dx,0),order=1,mode='nearest')[pad:-pad,pad:-pad]
  Bs,As=sh(base),sh(tA); I=img[y0:y1,x0:x1]
  d=(As-Bs).ravel(); a=float(np.dot(d,(I-Bs).ravel())/np.dot(d,d)); resid=np.sqrt(np.mean((Bs+a*(As-Bs)-I)**2))*255
  # doubled outline: rest seam pixels (dark in rest, i.e. base lips line) lying inside anger lips; and anger outline pixels outside rest lips
  lum=lambda X:X@[0.299,0.587,0.114]
  Lb,La,Li=lum(Bs),lum(As),lum(I)
  rest_line=(Lb<0.12)   # rest seam/line #220C00
  ang_line=(La<0.12)
  rest_only=rest_line&~binary_dilation(ang_line,iterations=1); ang_only=ang_line&~binary_dilation(rest_line,iterations=1)
  # visibility: fraction of full contrast still shown in the fade frame
  vis_rest=float(np.median((La[rest_only]-Li[rest_only])/(La[rest_only]-Lb[rest_only]+1e-6))) if rest_only.any() else None
  vis_ang=float(np.median((Lb[ang_only]-Li[ang_only])/(Lb[ang_only]-La[ang_only]+1e-6))) if ang_only.any() else None
  res[run]=dict(rows=rows,fade_f9=dict(alpha_in=round(a,3),resid=round(resid,2),rest_only_line_px=int(rest_only.sum()),anger_only_line_px=int(ang_only.sum()),
    rest_line_visibility=round(vis_rest,2) if vis_rest is not None else None,anger_line_visibility=round(vis_ang,2) if vis_ang is not None else None),
    picks={k:sum(1 for f in fr if f['mouth']==k) for k in set(f['mouth'] for f in fr)},talk_any=any(f['extra']['mouthTalk'] for f in fr),
    first_anger_t=next(f['t'] for f in fr if f['mouth']=='mouth_anger'),last_t=fr[-1]['t'],last_pick=fr[-1]['mouth'],nframes=len(fr),errs=len(m['errs']))
  print(run,json.dumps({k:v for k,v in res[run].items() if k!='rows'}));[print('  ',r) for r in rows]
json.dump(res,open('anger_clip_results.json','w'),indent=1)
