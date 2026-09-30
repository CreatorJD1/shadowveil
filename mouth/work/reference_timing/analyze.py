import json, csv, numpy as np
from PIL import Image, ImageDraw
CLIPS=['talk','idle','idle-long','smirk','tongue','cheeks','gasp','startle','glare','angry','worry','hem']
FPS=24; FR=1000/FPS
ours=json.load(open('tmp/ours.json'))
DESIGN_OPEN={'rest':0,'M':0,'smile':0,'OH_half':8.2,'AA_half':8.8,'EE_half':2.8,'OH':14.8,'AA':17.2,'EE':5.7}  # build5.py FRONT: Sl-Su at centre (apose px)
OW0=ours['rest']['W']
O={n:dict(w=v['W']/OW0,h=v['Hmouth']/OW0,o_meas=v['openH']/OW0,o=DESIGN_OPEN[n]/OW0,lift=v['cornerLift']/OW0) for n,v in ours.items()}
# her normalisation: rest-mouth width from idle, scaled per clip by the iris distance
idle=json.load(open('tmp/idle.json'))
W_REST_IDLE=float(np.median([x['W'] for x in idle])); ED_IDLE=float(np.median([x['eyeD'] for x in idle if x.get('eyeD')]))
H_REST_IDLE=float(np.median([x['Hmouth'] for x in idle])); L_REST_IDLE=float(np.median([x['cornerLift'] for x in idle]))
# grid thresholds from our own shapes (midpoints)
half=np.mean([O['OH_half']['o'],O['AA_half']['o']]); full=np.mean([O['OH']['o'],O['AA']['o']])
T_OPEN=(half/2,(half+full)/2)
T_FORM=((O['OH_half']['w']+O['AA_half']['w'])/2,(O['AA']['w']+O['EE']['w'])/2)
NAME={(0,-1):'M',(0,0):'rest',(0,1):'smile',(0.5,-1):'OH_half',(0.5,0):'AA_half',(0.5,1):'EE_half',(1,-1):'OH',(1,0):'AA',(1,1):'EE'}
def grid(o,w):
    op=0 if o<T_OPEN[0] else 0.5 if o<T_OPEN[1] else 1
    fm=-1 if w<T_FORM[0] else 1 if w>T_FORM[1] else 0
    return op,fm
rows=[]; per={}
for c in CLIPS:
    r=json.load(open(f'tmp/{c}.json')); ed=float(np.median([x['eyeD'] for x in r if x.get('ok') and x.get('eyeD')]))
    W0=W_REST_IDLE*ed/ED_IDLE; per[c]=dict(eyeD=ed,W0=W0,rows=[])
    for x in r:
        if not x['ok']: continue
        w=x['W']/W0; h=x['Hmouth']/W0; o=x['openH']/W0; lift=x['cornerLift']/W0
        op,fm=grid(o,w)
        d=dict(clip=c,frame=x['frame'],t_ms=x['t_ms'],W_px=x['W'],Hmouth_px=x['Hmouth'],openH_px=x['openH'],teeth_px=round(x['teeth'],1),
               tongue_px=round(x['tongue'],1),cornerLift_px=x['cornerLift'],roll_deg=x.get('roll'),eyeDist_px=x.get('eyeD'),frameDiff=x['frameDiff'],
               restW_px=round(W0,2),w=round(w,3),h=round(h,3),o=round(o,3),lift=round(lift,3),MouthOpen=op,MouthForm=fm,shape=NAME[(op,fm)])
        rows.append(d); per[c]['rows'].append(d)
with open('reference_mouth_frames.csv','w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
def runs(seq):
    out=[]; s=0
    for i in range(1,len(seq)+1):
        if i==len(seq) or seq[i]!=seq[s]: out.append((seq[s],i-s)); s=i
    return out
S={}
for c in CLIPS:
    R=per[c]['rows']; sh=[x['shape'] for x in R]; op=[x['MouthOpen'] for x in R]
    rr=runs(sh); holds=np.array([n for _,n in rr])*FR
    # new drawings: big pixel change in the fixed mouth window
    diffs=np.array([x['frameDiff'] for x in R]); newd=np.nonzero(diffs>8)[0]
    dh=np.diff(np.r_[0,newd,len(R)])*FR
    closes=[n for v,n in runs(op) if v==0]
    S[c]=dict(frames=len(R),dur_s=len(R)/FPS,shapeChanges=len(rr)-1,changesPerSec=(len(rr)-1)/(len(R)/FPS),
              holdMs=dict(min=float(holds.min()),p25=float(np.percentile(holds,25)),median=float(np.median(holds)),p75=float(np.percentile(holds,75)),max=float(holds.max()),mean=float(holds.mean())),
              holdHist={str(int(round(k))):int(v) for k,v in zip(*np.unique(np.round(holds),return_counts=True))},
              newDrawings=len(newd),drawingHoldMs=dict(median=float(np.median(dh)),p10=float(np.percentile(dh,10)),p90=float(np.percentile(dh,90))),
              repeatFrac=float((diffs[1:]<1.0).mean()),
              closedRuns=len(closes),closuresPerSec=len(closes)/(len(R)/FPS),closedRunMs=[float(n*FR) for n in closes][:20],
              openFrac={str(k):float(np.mean(np.array(op)==k)) for k in (0,0.5,1)},
              shapeFrac={k:float(np.mean(np.array(sh)==k)) for k in NAME.values() if np.mean(np.array(sh)==k)>0},
              w=dict(min=min(x['w'] for x in R),median=float(np.median([x['w'] for x in R])),max=max(x['w'] for x in R)),
              o=dict(median=float(np.median([x['o'] for x in R])),p90=float(np.percentile([x['o'] for x in R],90)),max=max(x['o'] for x in R)),
              h=dict(median=float(np.median([x['h'] for x in R])),max=max(x['h'] for x in R)),
              lift=dict(median=float(np.median([x['lift'] for x in R])),max=max(x['lift'] for x in R),min=min(x['lift'] for x in R)),
              teethFrames=int(sum(x['teeth_px']>8 for x in R)),eyeD=per[c]['eyeD'],restW=per[c]['W0'])
# talk: open-frame level stats
T=per['talk']['rows']; oo=np.array([x['o'] for x in T]); openf=oo[oo>=T_OPEN[0]]
S['talk']['openWhenOpen']=dict(median=float(np.median(openf)),p90=float(np.percentile(openf,90)),max=float(oo.max()))
S['talk']['fracOverOurFull']=float(np.mean(oo>O['AA']['o']))
json.dump(dict(ours=O,thresholds=dict(open=T_OPEN,form=T_FORM),rest=dict(W=W_REST_IDLE,eyeD=ED_IDLE,H=H_REST_IDLE,lift=L_REST_IDLE),clips=S),open('reference_stats.json','w'),indent=1)
print(json.dumps(dict(ours={k:{a:round(b,3) for a,b in v.items()} for k,v in O.items()},thr=(T_OPEN,T_FORM)),indent=0))
for c in CLIPS:
    s=S[c]; print(c,'chg/s %.1f'%s['changesPerSec'],'hold med %.0f p25 %.0f p75 %.0f min %.0f'%(s['holdMs']['median'],s['holdMs']['p25'],s['holdMs']['p75'],s['holdMs']['min']),
      'draw med %.0f'%s['drawingHoldMs']['median'],'rep %.2f'%s['repeatFrac'],'close/s %.2f'%s['closuresPerSec'],'open',{k:round(v,2) for k,v in s['openFrac'].items()},
      'w %.2f-%.2f'%(s['w']['min'],s['w']['max']),'o max %.2f'%s['o']['max'],'lift %.3f..%.3f'%(s['lift']['min'],s['lift']['max']),'teeth',s['teethFrames'])
print('talk hist',S['talk']['holdHist'],S['talk']['shapeFrac'],S['talk']['openWhenOpen'],S['talk']['fracOverOurFull'])
# ---- talk at drawing level (the video holds each mouth drawing ~3 frames): shape per drawing = shape of its middle frame
def drawing_level(R):
    diffs=np.array([x['frameDiff'] for x in R]); b=[0]+[i for i in range(1,len(R)) if diffs[i]>8]+[len(R)]
    seg=[(b[k],b[k+1]) for k in range(len(b)-1)]
    sh=[R[(s+e-1)//2]['shape'] for s,e in seg]; ln=[e-s for s,e in seg]
    merged=[]
    for s_,l_ in zip(sh,ln):
        if merged and merged[-1][0]==s_: merged[-1][1]+=l_
        else: merged.append([s_,l_])
    return seg,ln,merged
seg,ln,merged=drawing_level(T)
hm=np.array([l for _,l in merged])*FR
op_m=[(NAME_INV:=None) or s for s,_ in merged]
closedHold=[l*FR for s,l in merged if s in('rest','M','smile')]; openHold=[l*FR for s,l in merged if s not in('rest','M','smile')]
Wopen=[x['w'] for x in T if x['MouthOpen']>0]; Wclosed=[x['w'] for x in T if x['MouthOpen']==0]
S['talk']['drawings']=dict(count=len(seg),lenFramesHist={str(k):int(v) for k,v in zip(*np.unique(ln,return_counts=True))},
    shapeRuns=len(merged),shapeChangesPerSec=(len(merged)-1)/(len(T)/FPS),
    holdMs=dict(min=float(hm.min()),p25=float(np.percentile(hm,25)),median=float(np.median(hm)),p75=float(np.percentile(hm,75)),max=float(hm.max()),mean=float(hm.mean())),
    holdHist={str(int(round(k))):int(v) for k,v in zip(*np.unique(np.round(hm),return_counts=True))},
    closedHoldMs=dict(median=float(np.median(closedHold)),n=len(closedHold)),openHoldMs=dict(median=float(np.median(openHold)),n=len(openHold)),
    sequence=[(s,int(round(l*FR))) for s,l in merged])
S['talk']['wOpen']=dict(median=float(np.median(Wopen)),min=float(min(Wopen)),max=float(max(Wopen)));S['talk']['wClosed']=dict(median=float(np.median(Wclosed)))
json.dump(dict(ours=O,thresholds=dict(open=T_OPEN,form=T_FORM),rest=dict(W=W_REST_IDLE,eyeD=ED_IDLE,H=H_REST_IDLE,lift=L_REST_IDLE),clips=S),open('reference_stats.json','w'),indent=1)
print(json.dumps({k:v for k,v in S['talk']['drawings'].items() if k!='sequence'}),S['talk']['wOpen'],S['talk']['wClosed'])
print(S['talk']['drawings']['sequence'])
