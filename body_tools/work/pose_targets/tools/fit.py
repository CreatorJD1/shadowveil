# Benchmark keypoints (hand-read on a 100 px grid over each 1120x2240 benchmark; her L = image right) -> rig controls.
import json, math, os
OUT=os.path.join(os.path.dirname(__file__),'..','work','fit.json')
def ang(a,b,side):  # outward angle from straight down, deg (+ = away from body midline)
    dx,dy=b[0]-a[0],b[1]-a[1]; d=math.degrees(math.atan2(dx,dy)); return d if side=='L' else -d
# keypoints: sho, elb, wri, hip, knee, ank per side (px in benchmark image)
K={
1:dict(R=dict(sho=(390,520),elb=(250,720),wri=(120,880),hip=(450,1000),knee=(330,1450),ank=(230,1930)),
       L=dict(sho=(720,510),elb=(870,690),wri=(980,800),hip=(650,1000),knee=(720,1450),ank=(840,1920)),neck=(530,470),pel=(550,1000)),
2:dict(R=dict(sho=(300,500),elb=(150,760),wri=(420,860),hip=(380,1020),knee=(300,1450),ank=(230,1990)),
       L=dict(sho=(600,490),elb=(650,760),wri=(690,1050),hip=(560,1000),knee=(650,1440),ank=(760,1980)),neck=(450,470),pel=(470,1010)),
3:dict(R=dict(sho=(330,480),elb=(270,780),wri=(250,1070),hip=(420,1000),knee=(370,1460),ank=(330,1990)),
       L=dict(sho=(700,480),elb=(760,780),wri=(790,1060),hip=(600,1000),knee=(660,1460),ank=(690,1990)),neck=(515,460),pel=(510,1000)),
4:dict(R=dict(sho=(330,560),elb=(220,400),wri=(110,250),hip=(400,1070),knee=(310,1450),ank=(180,2000)),
       L=dict(sho=(640,540),elb=(760,330),wri=(930,100),hip=(590,1070),knee=(760,1530),ank=(900,1980)),neck=(520,480),pel=(485,1080)),
5:dict(R=dict(sho=(380,530),elb=(300,800),wri=(230,1080),hip=(440,1060),knee=(330,1480),ank=(260,2030)),
       L=dict(sho=(700,530),elb=(790,800),wri=(850,1080),hip=(640,1060),knee=(760,1480),ank=(830,2030)),neck=(540,500),pel=(540,1060)),
6:dict(R=dict(sho=(370,480),elb=(340,780),wri=(290,1080),hip=(430,1000),knee=(420,1470),ank=(400,2000)),
       L=dict(sho=(680,470),elb=(720,780),wri=(760,1080),hip=(600,1000),knee=(630,1470),ank=(660,2010)),neck=(525,460),pel=(515,1000)),
}
VIEW={1:'apose',2:'apose',3:'apose',4:'tpose',5:'apose',6:'apose'}
SK='/workspace/shadowveil/views/{}/body/skin.json'
def rest(view):
    B={b['name']:b for b in json.load(open(SK.format(view)))['bones']}
    P=lambda n:B[n]['pivot']; r={}
    for s in 'LR':
        wp=B['forearm_'+s]['wristPivot']; wp=(wp['x'],wp['y'])
        r[s]=dict(U=ang(P('upperArm_'+s),P('forearm_'+s),s),F=ang(P('forearm_'+s),wp,s),T=ang(P('thigh_'+s),P('shin_'+s),s),S=ang(P('shin_'+s),P('foot_'+s),s))
    return r
LIM=25.0
def fit(i):
    k=K[i]; v=VIEW[i]; R=rest(v); vals={}; tgt={}; resid={}
    for s in 'LR':
        q=k[s]; t=dict(U=ang(q['sho'],q['elb'],s),F=ang(q['elb'],q['wri'],s),T=ang(q['hip'],q['knee'],s),S=ang(q['knee'],q['ank'],s)); tgt[s]=t
        sg=-1 if s=='L' else 1   # screen rotation + = clockwise; her L limb (image right) abducts with -, her R with +
        dU=t['U']-R[s]['U']; dE=(t['F']-R[s]['F'])-dU; dH=t['T']-R[s]['T']; dK=(t['S']-R[s]['S'])-dH
        for name,d in (('Shoulder',dU),('Elbow',dE),('Hip',dH),('Knee',dK)):
            raw=sg*d/LIM; vals[name+s+'_raw']=round(raw,3)
        # feet flat: ankle cancels the leg's world rotation
    stress={k2[:-4]:v2 for k2,v2 in vals.items()}
    for s in 'LR': stress['Ankle'+s]=round(-(stress['Hip'+s]+stress['Knee'+s]),3)
    legal={k2:round(max(-1,min(1,v2)),3) for k2,v2 in stress.items()}
    for s in 'LR': legal['Ankle'+s]=round(max(-1,min(1,-(legal['Hip'+s]+legal['Knee'+s]))),3)
    lean=math.degrees(math.atan2(k['neck'][0]-k['pel'][0],k['pel'][1]-k['neck'][1]))   # + = top to image right = clockwise
    stress['BodyLean']=round(lean/8,3); legal['BodyLean']=round(max(-1,min(1,lean/8)),3)
    resid={kk:round((stress[kk]-legal[kk])*(8 if kk=='BodyLean' else LIM),1) for kk in stress if abs(stress[kk]-legal[kk])>1e-6}
    return dict(view=v,rest_deg=R,target_deg={s:{a:round(b,1) for a,b in tgt[s].items()} for s in tgt},lean_deg=round(lean,1),legal=legal,stress=stress,clamp_residual_deg=resid)
res={i:fit(i) for i in K}
json.dump(dict(keypoints=K,fit=res),open(OUT,'w'),indent=1)
for i,r in res.items(): print(i,r['view'],r['target_deg'],'\n  legal',r['legal'],'\n  resid',r['clamp_residual_deg'])
