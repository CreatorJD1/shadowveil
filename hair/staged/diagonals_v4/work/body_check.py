# PROVISIONAL hair-over-body check for diagonals_v4 frame_scale (Body's diag_body pieces may change; no body/head bends, hair sway only).
# 1) frame_scale rig.json: root hair parts parented to Body's "head" (parent neck, layer 242); hair layers above the head piece.
# 2) rest: Body pieces + Eyes rest parts (white, iris, lid_0, lash) + Mouth frame_scale/rest.png + frame_scale hair vs her frame f033/f191.
# 3) sway (caps applied, slider X x Y + per-segment chain drive): px the hair covers at rest that no layer covers at a sway state.
#    inside her keyed figure = see-through hole (Body underfill candidate); outside = her own background key (natural).
import json,glob,itertools,numpy as np
from sway_gate import *
from PIL import Image
HEAD={'045':(387,237),'315':(374,238)}; FRM={'045':'f033','315':'f191'}; res={}
for ang in ('045','315'):
    d,rig,parts,im=load(ang,'frame'); Bd=f'{R}/body_tools/work/diag_body/{ang}'; bj=json.load(open(f'{Bd}/parts.json'))
    for p in rig['parts']:
        if p.get('parent') is None: p['parent']='head'; p.pop('parentGroup',None)
    rig['headBone']=dict(id='head',parent='neck',layer=242,pivot=list(HEAD[ang]),source='body_tools/work/diag_body/'+ang+'/parts.json (provisional)',
                         note='hair roots parent to head; every hair layer draws above the head piece; hair over mouth (500) only where her frame has hair (rest overlap 0)')
    rig.pop('headGroup',None); json.dump(rig,open(f'{d}/rig.json','w'),indent=1)
    fr=A(f'{R}/reference/apose_turn/frames/{FRM[ang]}.png')[...,:3]; fig=np.array(Image.open(f'{Bd}/figure_keyed_full.png').convert('RGBA'))[...,3]>0
    comp=np.zeros((1168,768,3),int); cov=np.zeros((1168,768),bool); static=np.zeros((1168,768),bool); ov=np.zeros((1168,768),int)
    def put(a,st):
        global comp
        m=a[...,3]>0; comp[m]=a[m,:3]; ov[m]+=1; cov[m]=True
        if st: static[m]=True
    for p in sorted(bj['pieces'],key=lambda p:p['layer']): put(A(f"{Bd}/{p['file']}"),True)
    E=f'{R}/eyes/staged/diagonals/{ang}'
    for n in ('white','iris','lid_0','lash'):
        for g in glob.glob(f'{E}/Eye?_{n}.png'): put(A(g),True)
    put(A(f'{R}/mouth/staged/diag_posable/{ang}/frame_scale/rest.png'),True)
    hairrest=np.zeros((1168,768),bool)
    for p in sorted(parts,key=lambda p:p['layer']):
        a=A(f"{d}/{p['file']}"); put(a,False); hairrest|=a[...,3]>0
    diff=cov&(np.abs(comp-fr).max(-1)>0)
    rest=dict(diff_px_on_covered=int(diff.sum()),diff_px_hair=int((diff&hairrest).sum()),figure_px_uncovered=int((fig&~cov).sum()),overlap_px=int((ov>1).sum()),
              covered_outside_figure=int((cov&~fig).sum()),hair_px_outside_figure=int((hairrest&~fig).sum()))
    ys,xs=np.nonzero(fig&~cov); rest['uncovered_bbox']=[int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())] if len(ys) else None
    # sway coverage
    yy,xx=np.nonzero(np.ones((1168,768),bool)); bb=np.nonzero(nd.binary_dilation(hairrest,iterations=40))
    def hcov(xd,y):
        by={p['id']:p for p in parts}; Mm={}
        def m(i):
            if i in Mm: return Mm[i]
            p=by[i]; x=xd.get(i,0.0); up=p.get('degAtPlus1',(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)); dn=p.get('degAtMinus1',-up)
            a=x*up if x>=0 else abs(x)*dn; base=m(p['parent']) if p.get('parent') in by else np.eye(3); Mm[i]=base@rot(p['pivotX'],p['pivotY'],a); return Mm[i]
        c=np.zeros((1168,768),bool); Y_,X_=bb
        for p in parts:
            a=im[p['id']]
            if not a.any(): continue
            dyp=int(np.round(np.clip(y,-1,1)*min(max(p.get('swayY') or 0,0),1)*rig.get('swayYMaxPx',3))) if y else 0
            Mi=np.linalg.inv(np.array([[1,0,0],[0,1,dyp],[0,0,1]])@m(p['id']))
            sx=np.floor(Mi[0,0]*(X_+.5)+Mi[0,1]*(Y_+.5)+Mi[0,2]).astype(int); sy=np.floor(Mi[1,0]*(X_+.5)+Mi[1,1]*(Y_+.5)+Mi[1,2]).astype(int)
            ok=(sx>=0)&(sx<768)&(sy>=0)&(sy<1168); h=np.zeros(len(X_),bool); h[ok]=a[sy[ok],sx[ok]]; c[Y_[h],X_[h]]=True
        return c
    sw,chains=drives(parts); states=[({i:X for i in sw},y,'slider') for X in XS for y in YS]
    for r_,segs in chains.items():
        if len(segs)>1: states+=[(dict(zip(segs,xs)),y,'segments') for xs in itertools.product(XS[::2],repeat=len(segs)) for y in (-1,0,1)]
    need=np.zeros((1168,768),bool); bgun=np.zeros((1168,768),bool); worst=(0,None); kz=np.zeros((1168,768),bool); kz[200:236,400:420]=True
    keygap=kz&~fig; kg_cov=[]
    for xd,y,path in states:
        c=hcov(xd,y); hole=hairrest&~c&~static
        hin=hole&fig; need|=hin; bgun|=hole&~fig
        if hin.sum()>worst[0]: worst=(int(hin.sum()),dict(x={k:round(float(v),2) for k,v in xd.items()} if path=='segments' else round(float(list(xd.values())[0]),2),Y=y,path=path))
        kg_cov.append(int((keygap&c).sum()))
    os.makedirs(f'{O}/{ang}/for_base_body',exist_ok=True)
    Image.fromarray((need*255).astype(np.uint8)).save(f'{O}/{ang}/for_base_body/PROVISIONAL_skull_underfill_mask_frame.png')
    ys,xs=np.nonzero(need)
    res[ang]=dict(rest=rest,sway=dict(states=len(states),max_holes_inside_figure=worst[0],worst_state=worst[1],underfill_union_px=int(need.sum()),
                  underfill_bbox=[int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())] if len(ys) else None,background_px_uncovered_union=int(bgun.sum())),
                  key_gap_045=dict(region='x400-419 y200-235',her_frame_key_px=int(keygap.sum()),hair_over_it_rest=int((keygap&hairrest).sum()),hair_over_it_min_max_sway=[min(kg_cov),max(kg_cov)]) )
    print(ang,json.dumps(res[ang]),flush=True)
json.dump(res,open(f'{O}/body_check_PROVISIONAL.json','w'),indent=1)
