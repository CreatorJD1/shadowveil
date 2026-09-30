# line-art QA for rendered clips (v2 idle/Life/actions): outline width vs rest (|dWmed|<=1 px), breaks (+2 inner skeleton ends), kinks,
# at armpits, elbows, wrists, knuckles, hips, knees, ankles and hair tips. usage: lineart_frames.py <render dir> <out.json> [step]
import sys,os,json,math,numpy as np
from PIL import Image
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from lineart import roi_stats
d,out=sys.argv[1],sys.argv[2];step=int(sys.argv[3]) if len(sys.argv)>3 else 4
M=json.load(open(d+'/meta.json'));view=M['view'];V='/workspace/shadowveil/views/'+view
sk=json.load(open(V+'/body/skin.json'));B={b['name']:b for b in sk['bones']}
rest=np.array(Image.open(d+'/rest.png').convert('RGBA'))
def wrist(bs,H):
    b=B.get('forearm_'+H);wp=b and b.get('wristPivot')
    if not wp: return None
    wp=[wp['x'],wp['y']] if isinstance(wp,dict) else wp;x,y,a=bs['forearm_'+H];a=math.radians(a);dx,dy=wp[0]-b['pivot'][0],wp[1]-b['pivot'][1]
    return [x+dx*math.cos(a)-dy*math.sin(a),y+dx*math.sin(a)+dy*math.cos(a)]
tips=[]
try:
    hj=json.load(open(V+'/hair/rig.json'));hp=hj['parts'] if isinstance(hj,dict) else hj
    for p in hp:
        if p.get('file') and ('tip' in p['id']):
            a=np.array(Image.open(V+'/hair/'+p['file']))[...,3];ys,xs=np.nonzero(a>0)
            if len(ys): k=ys.argmax();tips.append((p['id'],[float(xs[k]),float(ys[k])]))
except Exception as e: pass
hidden={'left':'R','right':'L'}.get(view)
def rois(bs,restpose=False):
    o={}
    for H in 'LR':
        for nm,bn in [('armpit','upperArm_'),('elbow','forearm_'),('hip','thigh_'),('knee','shin_'),('ankle','foot_')]:
            if bn+H in bs: o[nm+'_'+H]=(bs[bn+H][:2],48)
        if H!=hidden:
            w=wrist(bs,H)
            if w: o['wrist_'+H]=(w,48);o['knuckle_'+H]=(w,80)
    h0=B['head']['pivot'] if 'head' in B else None
    for tid,(x,y) in tips:
        if h0 and 'head' in bs: dx,dy=bs['head'][0]-h0[0],bs['head'][1]-h0[1]
        else: dx=dy=0
        o['hairtip_'+tid]=([x+dx,y+dy],40)
    return o
restB={n:[b['pivot'][0],b['pivot'][1],0] for n,b in B.items()}
R0={k:roi_stats(rest,*c,r=r) for k,(c,r) in rois(restB).items()}
fr=sorted(os.listdir(d+'/frames'));res={k:dict(maxAbsDW=0,maxDEnds=0,maxDKinks=0,failFrames=[]) for k in R0}
for f in M['frames'][::step]:
    i=f['frame'];fn=d+'/frames/f%04d.png'%i
    if not os.path.exists(fn): continue
    im=np.array(Image.open(fn).convert('RGBA'))
    for k,(c,r) in rois(f['bones']).items():
        b=R0.get(k)
        if not b: continue
        s=roi_stats(im,*c,r=r)
        if not s: continue
        dw=s['wmed']-b['wmed'];de=s['comps']-b['comps'];dk=s['kinks']-b['kinks'];q=res[k]
        q['maxAbsDW']=max(q['maxAbsDW'],round(abs(dw),2));q['maxDEnds']=max(q['maxDEnds'],de);q['maxDKinks']=max(q['maxDKinks'],dk)
        why=[]
        if abs(dw)>1: why.append('width %+.2f'%dw)
        if de>=1: why.append('break +%d piece(s)'%de)
        if dk>max(6,0.25*b['kinks']): why.append('kinks +%d'%dk)
        if why: q['failFrames'].append([i,', '.join(why)])
json.dump(dict(dir=d,view=view,step=step,rest=R0,roi=res),open(out,'w'),indent=0)
bad={k:v for k,v in res.items() if v['failFrames']}
print(d,view,'ROIs',len(res),'failing ROIs',len(bad))
for k,v in bad.items(): print(' ',k,'maxDW',v['maxAbsDW'],'frames',len(v['failFrames']),v['failFrames'][:6])
