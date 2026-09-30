import json
S={'rest':(0,0),'M':(0,-1),'smile':(0,1),'OH_half':(0.5,-1),'AA_half':(0.5,0),'EE_half':(0.5,1),'OH':(1,-1),'AA':(1,0),'EE':(1,1),'anger':(0.25,-1)}  # anger: front views only (apose/tpose); profiles pick M there
eps=0.001
def build(seq,end):
    O=[];F=[]
    for i,(ts,s) in enumerate(seq):
        o,f=S[s]
        if i>0:
            po,pf=S[seq[i-1][1]];O.append([round(ts-eps,4),po]);F.append([round(ts-eps,4),pf])
        O.append([ts,o]);F.append([ts,f])
    lo,lf=S[seq[-1][1]];O.append([end,lo]);F.append([end,lf])
    return {'MouthOpen':O,'MouthForm':F}
clips={}
clips['jump']=dict(keys=build([(0,'rest'),(0.5,'AA_half'),(0.8,'OH_half'),(1.1,'M'),(1.3,'rest')],1.6),fps=30,duration=1.6,loop=False,interp='linear',
  notes='Body beats: rest through crouch; effort open AA_half at takeoff 0.50; OH_half at apex 0.80; lips press M on landing 1.10; rest from 1.30 to 1.60.')
run=[]
for k in range(3):
    b=round(k*0.6667,4); run+= [(b,'AA_half'),(round(b+0.4,4),'rest')]
clips['run']=dict(keys=build(run,2.0),fps=30,duration=2.0,loop=True,interp='linear',
  notes='breathing mouth: AA_half 0.40 s then rest 0.27 s on each 0.667 s stride, from foot contact; loops cleanly (starts AA_half, ends rest).')
clips['anger']=dict(keys=build([(0,'rest'),(0.3,'anger')],3.0),fps=30,duration=3.0,loop=False,interp='linear',
  notes='rest, then the anger mouth (MouthOpen 0.25, MouthForm -1; cut from the approved Clean-room anger art) from Body set-in (0.30) to the end. Front views show anger; left/right have no anger shape and pick M at this point.')
json.dump({'format':'shadowveil idle clips v1 (same schema as body_tools/idle/idle_clips.json)','spec':'value(t)=linear interpolation of keys[param]; hard steps via 1 ms ramps','generator':'python3 mouth/actions/make_mouth_actions.py','clips':clips},open('mouth_actions.json','w'),indent=1)
names=list(S)
def val(k,t):
    for a,b in zip(k,k[1:]):
        if a[0]<=t<=b[0]: return a[1]+(b[1]-a[1])*((t-a[0])/(b[0]-a[0]) if b[0]>a[0] else 0)
    return k[-1][1]
near=lambda o,f:min(names,key=lambda n:(round(((S[n][0]-o)**2+(S[n][1]-f)**2)**0.5,9),n!='rest',S[n][0],names.index(n)))  # renderer tie-break: rest, then more closed, then order
for n,c in clips.items():
    fr=[near(val(c['keys']['MouthOpen'],i/30),val(c['keys']['MouthForm'],i/30)) for i in range(int(c['duration']*30)+1)]
    runs=[];cur=fr[0];m=0
    for x in fr:
        if x==cur:m+=1
        else:runs.append((cur,m));cur=x;m=1
    runs.append((cur,m))
    print(n,[(r[0],round(r[1]*1000/30)) for r in runs])
