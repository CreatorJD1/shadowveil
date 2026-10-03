# anger clip with ?mouthfix=1: picks, switch-frame alpha (hard cut => incoming alpha 1 on its first frame, no doubled outline), per view/pass.
# adapted from mouth/qa/render_v2/work/anger_clip.py (read-only copy of its method)
import numpy as np, json, os, sys
from PIL import Image
from scipy.ndimage import shift as nshift
sys.path.insert(0,'/workspace/shadowveil/rig/work/mouthfix/qa'); from fitlib import *
R='/workspace/shadowveil/'; O=R+'rig/work/mouthfix/anger/'; res={}
lum=lambda X:X@[0.299,0.587,0.114]
for pass_ in ['normal','stress']:
 for view in ['apose','tpose','left','right']:
  run=f'{pass_}_anger_{view}'; W=O+run+'/'
  if not os.path.exists(W+'meta.json'): continue
  m=json.load(open(W+'meta.json')); fr=m['frames']
  picks={k:sum(1 for f in fr if f['mouth']==k) for k in set(f['mouth'] for f in fr)}
  sw=[i for i in range(1,len(fr)) if fr[i]['mouth']!=fr[i-1]['mouth']]
  B=np.asarray(Image.open(R+f'views/{view}/base.png').convert('RGBA')).astype(float)/255; base=white(B)
  rj=json.load(open(R+f'views/{view}/mouth/rig.json')); rows=[]
  for s in sw:
    a,bn=fr[s-1]['mouth'].replace('mouth_',''),fr[s]['mouth'].replace('mouth_','')
    bb=rj['partsBBox'];u=[min(bb[a][0],bb[bn][0])-4,min(bb[a][1],bb[bn][1])-4,max(bb[a][2],bb[bn][2])+5,max(bb[a][3],bb[bn][3])+5];box=tuple(u)
    SA=np.asarray(Image.open(R+f'views/{view}/mouth/{a}.png').convert('RGBA')).astype(float)/255
    SB=np.asarray(Image.open(R+f'views/{view}/mouth/{bn}.png').convert('RGBA')).astype(float)/255
    tA,tB=white(comp(B,SA)),white(comp(B,SB))
    nxt=min(s+1,len(fr)-1); img_n=load(W+f'frames/f{nxt:04d}.png'); _,dx,dy=fit(img_n,tB,box,rng=8.0 if view in ('left','right') else 3.0)
    x0,y0,x1,y1=box;pad=6
    def sh(T): return nshift(T[y0-pad:y1+pad,x0-pad:x1+pad],(dy,dx,0),order=1,mode='nearest')[pad:-pad,pad:-pad]
    As,Bs=sh(tA),sh(tB)
    for i in (s-1,s):
      I=load(W+f'frames/f{i:04d}.png')[y0:y1,x0:x1]; d=(Bs-As).ravel(); al=float(np.dot(d,(I-As).ravel())/max(np.dot(d,d),1e-9)); resid=float(np.sqrt(np.mean((As+al*(Bs-As)-I)**2))*255)
      # doubled outline: px dark in exactly one of the two shapes, still showing >25% of their contrast in the frame
      La,Lb,Li=lum(As),lum(Bs),lum(I); aon=(La<0.12)&(Lb>0.3); bon=(Lb<0.12)&(La>0.3)
      vis_a=float(np.median((Lb[aon]-Li[aon])/(Lb[aon]-La[aon]+1e-6))) if aon.any() else None
      vis_b=float(np.median((La[bon]-Li[bon])/(La[bon]-Lb[bon]+1e-6))) if bon.any() else None
      dbl=bool(vis_a is not None and vis_b is not None and vis_a>0.25 and vis_b>0.25)
      rows.append(dict(f=i,t=fr[i]['t'],sw=f'{a}>{bn}',which='before' if i<s else 'switch',alpha_to=round(al,3),resid=round(resid,2),vis_from=None if vis_a is None else round(vis_a,2),vis_to=None if vis_b is None else round(vis_b,2),doubled=dbl,fit_shift=[round(dx,2),round(dy,2)]))
  res[run]=dict(picks=picks,switches=len(sw),doubled_frames=sum(r['doubled'] for r in rows),rows=rows,talk_any=any(f['extra']['mouthTalk'] for f in fr),errs=len(m['errs']),nframes=len(fr),inFade_frames=sum(1 for f in fr if f['mouthPrev'] and f['t']*1000-f['mouthT0']<35 and False))
  print(run,json.dumps({k:v for k,v in res[run].items() if k!='rows'}));[print('  ',r) for r in rows]
json.dump(res,open(O+'anger_mf_results.json','w'),indent=1)
