import json, numpy as np, collections
Q='/workspace/shadowveil/rig/work/mouthfix/qa/'
S={}
for v in ['apose','tpose']:
  a=json.load(open(Q+f'final_{v}.json')); o={}
  o['rest']=a['rest']
  sw=a['sweep']; o['sweep']=dict(n=len(sw),pick_mismatch=[(x['open'],x['form'],x['pick'],x['expected']) for x in sw if x['pick']!=x['expected']],
     max_px_vs_ref=max(x['px_vs_ref'] for x in sw),blue_max=max(max(x['blue']) for x in sw),
     dwidth_max={k:max((x['dwidth_p90'] or 0) for x in sw if x['pick']==k) for k in set(x['pick'] for x in sw)},
     picks=[[x['pick'] for x in sw if x['form']==f] for f in (-1,0,1)])
  o['authored']=a['authored']
  def flick(rows):
    nf=[r for r in rows if not r['inFade']]; tog=0; mx=0
    for p,q in zip(rows,rows[1:]):
      if p['inFade'] or q['inFade'] or p['cur']!=q['cur']: continue
      d=abs(p['sharp']-q['sharp']); mx=max(mx,d); tog+=d>0.05
    return dict(nonfade=len(nf),sharp_min=min(r['sharp'] for r in nf),sharp_max=max(r['sharp'] for r in nf),toggles_gt5pct=tog,max_step=round(mx,3),
      exact_frames=sum(r['px_vs_ref']==0 for r in nf),notexact_frames=sum(r['px_vs_ref']>0 for r in nf),max_px_nonfade=max(r['px_vs_ref'] for r in nf))
  for key in ('timed','talkface','talk'):
    rows=a[key]; fades=[r for r in rows if r['inFade']]
    sw_events=sum(1 for p,q in zip(rows,rows[1:]) if q['cur']!=p['cur'])+(1 if rows and rows[0]['cur']!='rest' else 0)
    o[key]=dict(frames=len(rows),switches=sw_events,fade_frames=len(fades),flicker=flick(rows),blue_max=max(max(r['blue']) for r in rows),
      picks=dict(collections.Counter(r['cur'] for r in rows)),talk_flag=sum(bool(r['talk']) for r in rows),
      width_p90_max={k:max((r['width_p90'] or 0) for r in rows if r['cur']==k and not r['inFade']) for k in set(r['cur'] for r in rows)})
    if key!='talk':
      o[key]['doubled_frames']=sum(r['dbl']['doubled'] for r in fades)
      o[key]['fade_samples']=[(r['t'],r['from'],r['cur'],r.get('el'),r.get('aIn_rig'),r.get('aOut_rig'),r['fit']['aIn'],r['fit']['aOut'],r['dbl']['out_vis'],r['dbl']['in_vis'],r['dbl']['doubled'],r['px_vs_ref']) for r in fades]
  # fade step-through
  fd=collections.defaultdict(list)
  for r in a['fade']: fd[r['pair']].append(r)
  o['fade']={}
  for p,rows in fd.items():
    d=[r['el'] for r in rows if r['dbl']['doubled']]
    o['fade'][p]=dict(doubled_el=(min(d),max(d)) if d else None,
      series=[(r['el'],r['fit']['aIn'] if r['fit'] else None,r['fit']['aOut'] if r['fit'] else None,r['dbl']['out_vis'],r['dbl']['in_vis'],r['px_vs_to']) for r in rows],
      first_pure_to=min([r['el'] for r in rows if r['px_vs_to']==0 and r['el']>=0],default=None),blue_max=max(max(r['blue']) for r in rows))
  h=[x for x in (a['holds'] or [])]; o['holds']=dict(n=len(h),min=min(h) if h else None)
  S[v]=o
json.dump(S,open(Q+'summary.json','w'),indent=1,default=float)
for v,o in S.items():
  print('=====',v); print('rest',o['rest']); print('sweep',{k:o['sweep'][k] for k in o['sweep'] if k!='picks'}); print(' picks',o['sweep']['picks'])
  print('authored',{k:(x['width_p90'],x['line_T'],x['blue_only'],x['blue_key']) for k,x in o['authored'].items()})
  for key in ('timed','talkface','talk'): print(key,{k:o[key][k] for k in o[key] if k!='fade_samples'})
  for s in o['talkface']['fade_samples'][:12]: print('  tf',s)
  for p,x in o['fade'].items(): print('fade',p,x['doubled_el'],'first pure',x['first_pure_to'],'blue',x['blue_max'],[s[:3] for s in x['series'] if s[0] in (0,2.5,10,17.5,25,30,35)])
  print('holds',o['holds'])
