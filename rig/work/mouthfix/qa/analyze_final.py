from analyze import *
def fit_fade_m(F,base,P,C,mm):
  idx=mm; Fr=F[idx][:,:3].astype(float); b=base[idx].astype(float); p=P[idx].astype(float); c=C[idx].astype(float)
  def comp1(bg,top,a): ta=top[:,3:]/255*a; return np.concatenate([top[:,:3]*ta+bg[:,:3]*(1-ta),bg[:,3:]],1)
  best=(1e9,0,0)
  for ao in np.linspace(0,1,41):
    PB=comp1(b,p,ao)
    for ai in np.linspace(0,1,41):
      e=np.mean((comp1(PB,c,ai)[:,:3]-Fr)**2)
      if e<best[0]: best=(e,ai,ao)
  return dict(aIn=round(best[1],3),aOut=round(best[2],3),rmse=round(best[0]**.5,2))
def nd(a,b,mask): return int(np.sum(np.any(a!=b,-1)&mask))
for view in sys.argv[1:]:
  r=Run(view);m=r.m;T=m['tests'];base=r.ref['base'];shapes=[s[0] for s in m['info']['shapes']]
  mm0=np.zeros(base.shape[:2],bool)
  for s in shapes: mm0|=r.ref['only_'+s][...,3]>0
  mm=binary_dilation(mm0,iterations=3)
  res={'info':{k:m['info'][k] for k in ('quality','fade','hold','shapes')},'rest':dict(T['rest'])}
  res['rest']['mouth_px_vs_base']=nd(r.ld('rest_posed'),base,mm); res['rest']['restpath_mouth_px']=nd(r.ld('rest_restpath'),base,mm)
  res['rest']['crop_px_vs_base_outside_mouth']=nd(r.ld('rest_posed'),base,~mm)
  TS={s:min(0.16,float(lum(r.ref['only_'+s])[r.ref['only_'+s][...,3]>200].min())+0.06) for s in shapes}
  AW={s:(bin_width(r.ref[s],mm,TS[s]) or (None,None,0)) for s in shapes}; w0=AW['rest'][1]
  def keyblue(Y): return int(np.sum((Y[...,2]>100)&(Y[...,2]>np.maximum(Y[...,0],Y[...,1])+60)&(Y[...,3]>0)))
  res['authored']={s:dict(line_T=round(TS[s],3),width_med=AW[s][0],width_p90=AW[s][1],line_px=AW[s][2],blue_only=blue_px(r.ref['only_'+s]),blue_key=keyblue(r.ref['only_'+s])) for s in shapes}
  bb=lambda X:blue_spill(X,base,mm)
  nearest=lambda o,f:min(m['info']['shapes'],key=lambda s:(round(np.hypot(s[1]-o,s[2]-f)*1e9),0 if s[0]=='rest' else 1,s[1]))[0]
  sw=[]
  for e in T['sweep']:
    X=r.ld(e['name']);pk=e['pick'].replace('mouth_','');lw=bin_width(X,mm,TS[pk])
    sw.append(dict(open=e['open'],form=e['form'],pick=pk,expected=nearest(e['open'],e['form']),px_vs_ref=nd(X,r.ref[pk],mm),blue=bb(X),width_p90=lw[1] if lw else None,dwidth_p90=(lw[1]-w0) if (lw and w0) else None))
  res['sweep']=sw
  def seq(rows_in,fitfade=True):
    rows=[]
    for e in rows_in:
      X=r.ld(e['name']);cur=e['cur'].replace('mouth_','');ref=r.ref[cur];lw=bin_width(X,mm,TS[cur])
      row=dict(t=round(e['t'],4),open=e.get('open'),form=e.get('form'),cur=cur,inFade=e['inFade'],talk=e.get('talk'),blue=bb(X),sharp=round(sharp(X,mm)/sharp(ref,mm),3),px_vs_ref=nd(X,ref,mm),width_p90=lw[1] if lw else None,head=e.get('head'))
      if e['inFade']:
        pv=e['prev'].replace('mouth_','');row['from']=pv;row['dbl']=doubled2(X,r.ref[pv],ref,mm);row['el']=round(e['el'],2)
        if fitfade: row['fit']=fit_fade_m(X,base,r.ref['only_'+pv],r.ref['only_'+cur],mm)
        if 'aIn' in e: row['aIn_rig']=round(e['aIn'],3);row['aOut_rig']=round(e['aOut'],3)
      rows.append(row)
    return rows
  res['timed']=seq(T['timed']); res['talkface']=seq(T['talkface']); res['talk']=seq(T['talk'],fitfade=False)
  fd=[]
  for e in T['fade']:
    X=r.ld(e['name']);p,c=e['from'],e['to']
    fd.append(dict(pair=p+'>'+c,el=e['el'],fit=fit_fade_m(X,base,r.ref['only_'+p],r.ref['only_'+c],mm) if e['el']>=0 else None,dbl=doubled2(X,r.ref[p],r.ref[c],mm),blue=bb(X),px_vs_from=nd(X,r.ref[p],mm),px_vs_to=nd(X,r.ref[c],mm)))
  res['fade']=fd; res['holds']=m['holds']; res['http_errors']=sorted(set(l for l in m['logs'] if l.startswith('http')))
  json.dump(res,open(Q+f'final_{view}.json','w'),indent=1,default=float);print(view,'done',flush=True)
