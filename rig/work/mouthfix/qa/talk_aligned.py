from analyze import *
from scipy.ndimage import affine_transform
out={}
for v in ['apose','tpose']:
  r=Run(v);m=r.m;b=m['box'];base=r.ref['base'];shapes=[s[0] for s in m['info']['shapes']]
  mm0=np.zeros(base.shape[:2],bool)
  for s in shapes: mm0|=r.ref['only_'+s][...,3]>0
  mm=binary_dilation(mm0,iterations=3)
  TS={s:min(0.16,float(lum(r.ref['only_'+s])[r.ref['only_'+s][...,3]>200].min())+0.06) for s in shapes}
  rows=[]
  for e in m['tests']['talk']:
    M=e['head'];A=np.array([[M[0],M[2],M[4]],[M[1],M[3],M[5]],[0,0,1]]);Ai=np.linalg.inv(A)
    # crop pixel (y,x) -> global (x+b0,y+b1) -> ref global Ai -> ref crop
    # affine_transform maps output coords o to input coords: in = Mat @ o + off  (in (row,col))
    Mat=np.array([[Ai[1,1],Ai[1,0]],[Ai[0,1],Ai[0,0]]])
    off=np.array([Ai[1,0]*b[0]+Ai[1,1]*b[1]+Ai[1,2]-b[1], Ai[0,0]*b[0]+Ai[0,1]*b[1]+Ai[0,2]-b[0]])
    cur=e['cur'].replace('mouth_','');ref=r.ref[cur].astype(float)
    wm=affine_transform(mm.astype(float),Mat,off,order=0)>0.5
    wref=np.stack([affine_transform(ref[...,k],Mat,off,order=1,mode='nearest') for k in range(4)],-1)
    X=r.ld(e['name'])
    s_act=sharp(X,wm); s_ref=sharp(r.ref[cur],mm); s_bil=sharp(wref,wm)
    exact=abs(M[1])<1e-9 and abs(M[0]-1)<1e-9
    dx=M[0]*681+M[2]*286+M[4]-681
    lw=bin_width(X,wm,TS[cur])
    rows.append(dict(t=e['t'],cur=cur,inFade=e['inFade'],sharp=round(s_act/s_ref,3),sharp_bilinear_model=round(s_bil/s_ref,3),rot=round(float(np.degrees(np.arctan2(M[1],M[0]))),3),dx=round(dx,3),axis=exact,
      blue=blue_spill(X,affine_transform(base[...,0].astype(float),Mat,off,order=0).astype(int)[...,None].repeat(4,-1)*0,wm),width_p90=lw[1] if lw else None,rmse_vs_bilinear=round(float(np.sqrt(np.mean(((X-wref)[wm][:,:3])**2))),2)))
  out[v]=rows
  nf=[x for x in rows if not x['inFade']];tog=[];mx=0
  for p,q in zip(rows,rows[1:]):
    if p['inFade'] or q['inFade'] or p['cur']!=q['cur']: continue
    d=abs(p['sharp']-q['sharp']);mx=max(mx,d)
    if d>0.05: tog.append((round(q['t'],3),p['sharp'],q['sharp'],p['rot'],q['rot']))
  print(v,'sharp range',min(x['sharp'] for x in nf),max(x['sharp'] for x in nf),'model range',min(x['sharp_bilinear_model'] for x in nf),max(x['sharp_bilinear_model'] for x in nf),'toggles>5%',len(tog),'max step',round(mx,3))
  print(' axis frames',[(round(x['t'],3),x['sharp'],x['dx']) for x in rows if x['axis']])
  print(' toggles',tog[:12])
  print(' width p90 by shape',{s:max((x['width_p90'] or 0) for x in nf if x['cur']==s) for s in set(x['cur'] for x in nf)},'none_frames',sum(x['width_p90'] is None for x in nf))
  print(' rmse vs bilinear model median',np.median([x['rmse_vs_bilinear'] for x in nf]),'blue max',max(max(x['blue']) for x in rows))
json.dump(out,open(Q+'talk_aligned.json','w'),indent=1,default=float)
