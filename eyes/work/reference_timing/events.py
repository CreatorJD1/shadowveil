import json,glob,os,numpy as np,csv
FPS=24; ms=lambda n: round(n*1000/FPS)
def runs(b):
    out=[];i=0
    while i<len(b):
        if b[i]:
            j=i
            while j+1<len(b) and b[j+1]: j+=1
            out.append((i,j)); i=j+1
        else: i+=1
    return out
res={}
for f in sorted(glob.glob('raw/*.json')):
    r=json.load(open(f)); c=r['clip']
    if r.get('eyes',1) is None or 'rows' not in r: res[c]=dict(eyes=False); continue
    rows=r['rows']; n=len(rows); info=dict(eyes=True,frames=n,boxes=r['boxes'],track_min=min(x['track'] for x in rows))
    # unique frames (held frames): face_diff below 0.4 counts as a repeat
    fd=np.array([x['face_diff'] if x['face_diff'] is not None else 99 for x in rows])
    info['unique_frames']=int((fd>0.4).sum()); info['median_face_diff']=float(np.median(fd[1:]))
    ev={}
    for E in 'RL':
        if E+'_white' not in rows[0]: continue
        w=np.array([x[E+'_white'] for x in rows],float); ref=np.percentile(w,90)
        info[E+'_white_ref']=float(ref)
        if ref<15: info[E+'_note']='eye too small/unclear'; continue
        o=w/ref; info[E+'_open']=[round(float(v),2) for v in o]
        evs=[]
        for a,b in runs(o<0.5):
            if o[a:b+1].min()>0.3: continue
            s=a
            while s>0 and o[s-1]<0.85 and a-s<6: s-=1
            s=s-1 if s>0 else s                      # last fully open frame before the close starts
            e=b
            while e+1<n and o[e+1]<0.85 and e-b<8: e+=1
            e=e+1 if e+1<n else e                     # first frame back to open
            cl=[i for i in range(s,e+1) if o[i]<0.15]
            if cl: c0,c1=cl[0],cl[-1]
            else: c0=c1=int(s+np.argmin(o[s:e+1]))
            evs.append(dict(start=s,closed_first=c0,closed_last=c1,reopen=e,min_open=round(float(o[s:e+1].min()),2),
                            close_ms=ms(c0-s),hold_ms=ms(c1-c0+1),open_ms=ms(e-c1),total_ms=ms(e-s),
                            track=round(float(min(rows[i]['track'] for i in range(s,e+1))),2)))
        ev[E]=evs
    info['events']=ev
    # gaze: iris x offset (fraction of eye width), both eyes averaged where available
    gx=[]
    for x in rows:
        v=[x[E+'_iris_x'] for E in 'RL' if x.get(E+'_iris_x') is not None and x.get(E+'_iris',0)>=6]
        gx.append(float(np.mean(v)) if v else np.nan)
    info['gaze_x']=[None if np.isnan(v) else round(v,3) for v in gx]
    info['head_dx']=[x['head_dx'] for x in rows]; info['head_dy']=[x['head_dy'] for x in rows]
    res[c]=info
json.dump(res,open('events.json','w'))
for c,i in res.items():
    if not i['eyes']: print(c,'no eyes'); continue
    print(c,'uniq',i['unique_frames'],'/',i['frames'],'trk',round(i['track_min'],2),'ref',{E:round(i.get(E+'_white_ref',0)) for E in 'RL'},
          {E:[(e['start'],e['closed_first'],e['closed_last'],e['reopen'],e['min_open'],e['track']) for e in v] for E,v in i['events'].items()})
