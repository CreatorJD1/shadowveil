"""Nearest-shape simulation mirroring rig/index.html mouthPick(): key=[round(dist*1e9), rest?0:1... (rest preferred), open, manifest idx]."""
import json,math,random; import numpy as np
ROOT='/workspace/shadowveil'
def shapes(view):
    r=json.load(open(f'{ROOT}/views/{view}/mouth/rig.json')); g=r['grid']; out=[]
    for i,p in enumerate(r['parts']):
        n=p['id'][6:]; o=g[n]; out.append(dict(name=n,open=o['MouthOpen'],form=o['MouthForm'],idx=i))
    return out
def pick(S,mo,mf,talk=False,excl=('EE','EE_half','smile')):
    if talk: S=[s for s in S if s['name'] not in excl]
    mo=min(max(mo,0),1); mf=min(max(mf,-1),1)
    return min(S,key=lambda s:(round(math.hypot(s['open']-mo,s['form']-mf)*1e9),0 if s['name']=='rest' else 1,s['open'],s['idx']))['name']
def val(k,t):
    if t<=k[0][0]: return k[0][1]
    for a,b in zip(k,k[1:]):
        if a[0]<=t<=b[0]: return a[1]+(b[1]-a[1])*((t-a[0])/(b[0]-a[0]) if b[0]>a[0] else 0)
    return k[-1][1]
def runs(seq):
    out=[];cur=seq[0];m=0
    for x in seq:
        if x==cur:m+=1
        else: out.append([cur,m]);cur=x;m=1
    out.append([cur,m]); return out
BEFORE=[s for s in shapes('apose') if s['name']!='anger']; AFTER=shapes('apose'); PROF=shapes('left')
res={}
# 1. grid points
gp={}
for s in AFTER:
    gp[s['name']]=dict(point=[s['open'],s['form']],before=pick(BEFORE,s['open'],s['form']),frontAfter=pick(AFTER,s['open'],s['form']),profile=pick(PROF,s['open'],s['form']),
                       talkBefore=pick(BEFORE,s['open'],s['form'],True),talkAfter=pick(AFTER,s['open'],s['form'],True))
res['gridPoints']=gp
# 2/3. clips at 30 fps and dense
clips={'mouth_showcase':json.load(open(f'{ROOT}/mouth/showcase/mouth_showcase.json'))['clips']['mouth_showcase']}
A=json.load(open(f'{ROOT}/mouth/actions/mouth_actions.json'))['clips']; B=json.load(open('backup/mouth_actions.json'))['clips']
for n in ('jump','run','anger'): clips[n]=A[n]
res['clips']={}
for n,c in clips.items():
    ko,kf=c['keys']['MouthOpen'],c['keys']['MouthForm']; N=int(round(c['duration']*30))+1
    fr=[(val(ko,i/30),val(kf,i/30)) for i in range(N)]
    pb=[pick(BEFORE,*x) for x in fr]; pa=[pick(AFTER,*x) for x in fr]; pp=[pick(PROF,*x) for x in fr]
    e=dict(frames=N,frontAfter_runs_ms=[[a,round(m*1000/30)] for a,m in runs(pa)],profile_runs_ms=[[a,round(m*1000/30)] for a,m in runs(pp)],
           framesChangedVsBefore=[i for i in range(N) if pa[i]!=pb[i]])
    if n=='anger':   # compare with the previous (M stand-in) keys
        ko0,kf0=B['anger']['keys']['MouthOpen'],B['anger']['keys']['MouthForm']
        e['previousKeys_runs_ms']=[[a,round(m*1000/30)] for a,m in runs([pick(BEFORE,val(ko0,i/30),val(kf0,i/30)) for i in range(N)])]
    # dense (0.1 ms) exposure: time where the front would show anger although it did not before
    ts=np.arange(0,c['duration'],1e-4); da=0.0; spans=[]
    for t in ts:
        x=(val(ko,t),val(kf,t)); 
        if pick(AFTER,*x)=='anger' and pick(BEFORE,*x)!='anger' and n!='anger':
            da+=1e-4; spans.append(round(t,4))
    e['dense_newAnger_ms']=round(da*1000,2); e['dense_newAnger_at_s']=sorted(set(round(t,3) for t in spans))[:20]
    res['clips'][n]=e
# 5. procedural talk (port of stepTalk, 60 fps), with the current TALK_EXCLUDE and with 'anger' added
def talk_sim(seed,secs=120,dt=1/60):
    r=random.Random(seed).random; k=dict(mode='pause',until=0.0,open=0.0,form=0.0,left=0,t0=0,dur=0,peak=0,f0=0,f1=0); forms=[-1,-0.5,0,0,0.5,1]
    sm=lambda u:u*u*(3-2*u); out=[]
    for i in range(int(secs/dt)):
        t=i*dt
        if k['mode']=='pause':
            u=min(max(dt/0.12,0),1); k['open']+=(0-k['open'])*u; k['form']+=(0-k['form'])*min(max(dt/0.25,0),1)
            if t>=k['until']: k.update(mode='syl',left=3+int(r()*8),t0=t,dur=0)
        if k['mode']=='syl':
            if t>=k['t0']+k['dur']:
                if k['left']<=0: k.update(mode='pause',until=t+0.35+r()*1.1)
                else:
                    k['left']-=1; k['t0']=t+(0.03+r()*0.06 if r()<0.25 else 0); k['dur']=0.13+r()*0.14; k['peak']=0.35+r()*0.65; k['f0']=k['form']; k['f1']=forms[int(r()*len(forms))]
            if k['mode']=='syl':
                u=min(max((t-k['t0'])/k['dur'],0),1)
                k['open']=max(0,k['open']-dt*6) if t<k['t0'] else k['peak']*math.sin(math.pi*u)**1.4
                k['form']=k['f0']+(k['f1']-k['f0'])*sm(min(max(u/0.45,0),1))
        out.append((k['open'],k['form']))
    return out
tot=chg=chg2=0
for seed in range(20):
    fr=talk_sim(seed)
    for x in fr:
        b=pick(BEFORE,*x,talk=True); a=pick(AFTER,*x,talk=True); a2=pick(AFTER,*x,talk=True,excl=('EE','EE_half','smile','anger'))
        tot+=1; chg+=(a!=b); chg2+=(a2!=b)
res['proceduralTalk']=dict(note='port of stepTalk() at 60 fps, 20 seeds x 120 s, instantaneous pick (no 120 ms hold)',frames=tot,
    framesPickingAngerWithCurrentTALK_EXCLUDE=chg,pct=round(100*chg/tot,2),framesChangedWithAngerAddedToTALK_EXCLUDE=chg2)
json.dump(res,open('nearest_sim.json','w'),indent=1)
print(json.dumps(res['gridPoints'],indent=0))
for n,e in res['clips'].items(): print(n,'changed frames',e['framesChangedVsBefore'],'front',e['frontAfter_runs_ms'][:12],'| profile',e['profile_runs_ms'][:6],'| dense new anger ms',e['dense_newAnger_ms'],e['dense_newAnger_at_s'], e.get('previousKeys_runs_ms',''))
print(res['proceduralTalk'])
