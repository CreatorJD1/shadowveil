import numpy as np, json, math, sys, os
from PIL import Image
from scipy import ndimage as nd
from measure3q import all_metrics, load, bbox, ROOT
VIEWS={v:all_metrics(f'{ROOT}/views/{v}/base.png') for v in ['apose','left','right','back']}
c=s=math.cos(math.radians(45))
def ell(a,b): return 2*math.sqrt((a/2*c)**2+(b/2*s)**2)
def proj(L,alpha): al=math.radians(alpha); return L*math.sqrt(math.cos(al)**2+(math.sin(al)*c)**2)
# her own hand lengths from the staged wrist cuts (tip = arm-proxy fingertip), for proxy calibration
def wrist_true(view,side,tip):
    d=json.load(open(f'{ROOT}/body_tools/work/hairless_division_staged/{view}/wrist_line_{side}.json'))['line']
    mx,my=(d[0][0]+d[1][0])/2,(d[0][1]+d[1][1])/2; return math.hypot(tip[0]-mx,tip[1]-my)
sys.path.insert(0,'/workspace/shadowveil/body_tools/work/apose_turn'); from measure import measure
CAL={}
for v in ['apose','back']:
    m=load(f'{ROOT}/views/{v}/base.png')[...,3]>0; o=measure(m)
    for k,arm in o['arms'].items():
        side={'apose':{'R':'R','L':'L'},'back':{'R':'L','L':'R'}}[v][k]   # back: viewer-left arm is her left
        try: CAL[(v,k)]=wrist_true(v,side,arm['tip'])-VIEWS[v]['arms'][k]['hand_len']
        except Exception: pass
cal_off=float(np.mean(list(CAL.values())))
ANGV={'045':('apose','left',46.0,1682),'315':('apose','right',46.0,1682),'135':('back','left',43.8,1681),'225':('back','right',43.8,1681)}
def chk(val,lo,hi,tol=1.0):
    if val is None: return dict(value=None,expected=[lo,hi],pass_=False,note='not measurable')
    return dict(value=round(val,1),expected=[round(lo,1),round(hi,1)],pass_=bool(lo-tol<=val<=hi+tol))
def evaluate(ang,png,post_json):
    fv,sv,alpha,foot=ANGV[ang]; rear=ang in('135','225'); F,S=VIEWS[fv],VIEWS[sv]
    a=load(png); m=a[...,3]>0; M=all_metrics(png); P=json.load(open(post_json))
    pal={tuple(v) for v in P['palette'].values()}
    # her exact eye tones (staged eye parts, cut from the turn frame by Eyes)
    eye_t=set()
    if not rear:
        d=f'{ROOT}/eyes/staged/diagonals/{ang}/'
        for f in os.listdir(d):
            if f.endswith('.png') and 'chroma' not in f:
                e=np.array(Image.open(d+f).convert('RGBA')); eye_t|={tuple(x) for x in e[e[...,3]>127][:,:3].tolist()}
    cols=a[m][:,:3]; u,n=np.unique(cols,axis=0,return_counts=True)
    off=sum(int(k) for c_,k in zip(map(tuple,u.tolist()),n) if c_ not in pal|eye_t)
    alpha_partial=int(((a[...,3]>0)&(a[...,3]<255)).sum())
    rgb=a[...,:3].astype(int)
    fringe=int((m&(((rgb[...,0]>150)&(rgb[...,2]>150)&(rgb[...,1]<110))|((rgb[...,2]-np.maximum(rgb[...,0],rgb[...,1]))>120))).sum())
    R={}
    R['crown_y']=chk(M['top'],40,40,0); R['foot_line_y']=chk(M['foot'],foot,foot,0)
    R['head_height']=chk(M['head_h'],min(F['head_h'],S['head_h']),max(F['head_h'],S['head_h'])) if not rear else dict(value=M['head_h'],pass_=False,note='chin hidden at rear 3/4 (and in her back view); not measurable')
    R['shoulder_width']=chk(M['shoulder_w'],ell(F['shoulder_w'],S['shoulder_w']),ell(F['shoulder_w'],S['shoulder_w']))
    R['leg_length']=chk(M['leg_len'],F['leg_len'],F['leg_len'])
    for side in ('R','L'):
        arm=M['arms'].get(side); fa=F['arms'][side]
        if not arm:
            R[f'arm_{side}']=dict(pass_=False,note='arm not separated from torso / hand missing'); continue
        R[f'arm_{side}_reach']=chk(arm['reach'],proj(fa['reach'],alpha),proj(fa['reach'],alpha))
        R[f'arm_{side}_armpit_to_wrist']=chk(arm['armpit_to_wrist'],proj(fa['armpit_to_wrist'],alpha),proj(fa['armpit_to_wrist'],alpha))
        R[f'forearm_{side}']=dict(value=None,pass_=False,note='elbow not locatable on a silhouette; upper arm/forearm split unverified')
        hl=arm['hand_len']+cal_off
        R[f'hand_{side}_len_wrist_to_tip']=chk(hl,146,156,0); R[f'hand_{side}_len_wrist_to_tip']['proxy_raw']=arm['hand_len']; R[f'hand_{side}_len_wrist_to_tip']['calib_offset']=round(cal_off,1)
        R[f'hand_{side}_finger_runs']=dict(value=arm['finger_runs'],her_views={'front':fa['finger_runs']},pass_=None,note='silhouette proxy only; five-finger shape judged visually')
    ft=M['feet']; exp=ell(F['feet'][0]['len_x'],max(f['len_x'] for f in S['feet']))
    R['feet_count']=dict(value=len(ft),expected=2,pass_=len(ft)==2)
    for i,f_ in enumerate(ft[:2]): R[f'foot_{i}_len_proj']=chk(f_['len_x'],exp,exp)
    R['bun_width_crown+30']=chk(M['bun_w_at_crown30'],min(v['bun_w_at_crown30'] for v in VIEWS.values()),max(v['bun_w_at_crown30'] for v in VIEWS.values()),0)
    R['off_palette_px']=dict(value=off,expected=0,pass_=off==0)
    R['partial_alpha_px']=dict(value=alpha_partial,expected=0,pass_=alpha_partial==0)
    R['chroma_fringe_px']=dict(value=fringe,expected=0,pass_=fringe==0)
    # eyes
    if rear:
        R['eyes']=dict(value='none drawn',pass_=True,note='rear 3/4: no eye invented')
        lip=int(np.all(a[...,:3]==P['palette']['lip'],-1)[m].sum())
        R['mouth']=dict(value=f'{lip} lip px',pass_=lip==0,note='rear 3/4: no mouth allowed')
    else:
        am=np.zeros(m.shape,bool); gm=np.zeros(m.shape,bool)
        hsv=np.array(Image.fromarray(a[...,:3]).convert('HSV')).astype(int)
        sat=(hsv[...,1]>90)&(hsv[...,2]>90)&m
        am=sat&(hsv[...,0]>=15)&(hsv[...,0]<=40); gm=sat&(hsv[...,0]>=55)&(hsv[...,0]<=120)
        am&=(np.mgrid[0:m.shape[0],0:m.shape[1]][0]<300); gm&=(np.mgrid[0:m.shape[0],0:m.shape[1]][0]<300)
        ax_=np.nonzero(am)[1].mean() if am.any() else None; gx_=np.nonzero(gm)[1].mean() if gm.any() else None
        ok=ax_ is not None and gx_ is not None and ax_<gx_
        R['eyes']=dict(amber_x=None if ax_ is None else round(ax_,1),green_x=None if gx_ is None else round(gx_,1),pass_=ok,
                       note='staged Eyes diagonal parts (lid_0 + lash + white + iris) pasted nearest-neighbour; amber must be viewer-left = her right (not mirrored)')
        lipm=np.all(a[...,:3]==P['palette']['lip'],-1)&m; bb=bbox(lipm)
        eyes_y=(np.nonzero(am|gm)[0].mean()) if (am|gm).any() else None
        if bb and eyes_y:
            mw=bb[2]-bb[0]+1; mc=(bb[1]+bb[3])/2; dy=mc-eyes_y
            R['mouth_width']=chk(mw,27,54,0); R['mouth_below_eyes']=chk(dy,57.5,58.5,1)
        else: R['mouth_width']=dict(value=None,pass_=False,note='no closed mouth detected')
    R['widow_peak_white_line']=dict(value=0,pass_=False,note='palette snap has no light hairline-rim tone; her faint white line is not reproduced')
    hard=[k for k,v in R.items() if v.get('pass_') is False]
    return dict(angle=ang,png=png,metrics=M,checks=R,failed=hard,n_fail=len(hard))
if __name__=='__main__':
    res={}
    for spec in sys.argv[1:]:
        ang,png=spec.split(':'); r=evaluate(ang,png,png.replace('.png','_post.json')); res[png]=r
        print(ang,png,'fails',r['n_fail'],r['failed'])
    json.dump(dict(views=VIEWS,cal_offsets={f'{k[0]}_{k[1]}':round(v,1) for k,v in CAL.items()},results=res),open('eval_all.json','w'),indent=1,default=str)
