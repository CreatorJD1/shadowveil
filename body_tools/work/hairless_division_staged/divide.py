# Base Body staged: Live2D-style piece division of hairless_<view>.png (apose, tpose, left, right, back). Writes ONLY under body_tools/work/hairless_division_staged/<view>/.
# Usage: python3 divide.py [apose|tpose|left|right|back]
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
ROOT='/workspace/shadowveil'; V=(sys.argv[1:] or ['apose'])[0]; OUT=f'{ROOT}/body_tools/work/hairless_division_staged/{V}'
PD=f'{OUT}/pieces'; os.makedirs(PD,exist_ok=True)
h=np.array(Image.open(f'{OUT}/hairless_{V}.png')).astype(np.int32); Hh,W=h.shape[:2]
h_a0rgb=int(((h[...,3]==0)&(h[...,:3]!=0).any(-1)).sum()); h[h[...,3]==0]=0   # transparent px: RGB is meaningless (left/right/back hairless keep her source bytes there); pieces store rgba 0
A=h[...,3]>0
lab=np.load(f'{ROOT}/body_tools/work/lab_{V}.npy')
rig=json.load(open(f'{ROOT}/views/{V}/body/rig.json')); rp={p['id']:p for p in rig['parts']}
hairrep=json.load(open(f'{OUT}/hairless_report.json')); SKIN=np.array(hairrep['skin_rgb']); LINE=np.array(hairrep['line_rgb'])
hand=np.array(Image.open(f'{ROOT}/hands/{V}_hand_erase_mask.png'))>127
OLD=['head','torso','pelvis','upperArm_L','upperArm_R','forearm_L','forearm_R','thigh_L','thigh_R','shin_L','shin_R','foot_L','foot_R']
NAME={'upperArm_L':'upper_arm_L','upperArm_R':'upper_arm_R'}
P={}
if V in ('left','right','back'):   # lab_<view>.npy indices follow views/<view>/body/rig.json part order (incl. toes); profile views carry one side only
    OLD=[p['id'] for p in rig['parts']]
    NAME.update({'toes_L':'foot_L','toes_R':'foot_R'})   # toes are not separate pieces: merged into the foot
for i,o in enumerate(OLD):
    q=(lab==i)&A&~hand; k_=NAME.get(o,o)
    if q.any() or k_ in ('head','torso','pelvis'): P[k_]=P.get(k_,np.zeros_like(q))|q
unl=A&(lab<0)&~hand; P['head']|=unl            # new cranium pixels -> head
# neck: head-label pixels below the jaw line (the jaw line itself stays on the head)
VC={'apose':dict(jaw=[(560,240),(605,255),(613,265),(625,287),(645,305),(668,320),(682,323),(697,320),(717,305),(735,287),(748,268),(760,255),(800,240)],
                 neck=[681.5,362.0],head=[681.5,318.0],mid=681.5,
                 neck_src='NEW: neck-base centre on the live neck line y=364',head_src='NEW: chin/neck junction on the midline'),
    'tpose':dict(jaw=[(560,245),(605,255),(616,262),(624,262),(628,270),(632,277),(636,284),(640,292),(652,298),(660,304),(670,311),(681,316),
                      (690,313),(700,307),(709,301),(717,295),(721,294),(729,284),(733,277),(737,269),(741,263),(749,258),(760,255),(800,245)],
                 neck=[681.5,354.0],head=[681.5,309.0],mid=681.0,
                 neck_src='NEW: neck-base centre on the T-pose neck line (torso label starts y356; neck outlines x643/x720 -> centre 681.5)',
                 head_src='NEW: chin/neck junction on the midline (T-pose chin line y312-313, pivot 3-4 px inside the chin as A-pose)')}.get(V)
if VC is None:   # left/right/back: <view>/divide_config.json (jaw polyline, neck/head pivots, hip midline, layers from the live rig)
    VC=json.load(open(f'{OUT}/divide_config.json')); VC['jaw']=[tuple(p) for p in VC['jaw']]
jaw=VC['jaw']   # 2-3 px below her jaw/chin outline: the outline stays on the head
yy,xx=np.mgrid[0:Hh,0:W]; jy=np.interp(xx,[p[0] for p in jaw],[p[1] for p in jaw])
neck=P['head']&(yy>jy)
nl,nn=ndimage.label(neck,structure=np.ones((3,3))); neck=nl==(np.argmax(ndimage.sum(neck,nl,range(1,nn+1)))+1)   # main neck only; stray specks stay on the head
P['neck']=neck; P['head']=P['head']&~neck
# layers (back->front), same bands as the live rig; neck sits under torso and head
LAYER={'foot_L':201,'foot_R':201,'shin_L':203,'shin_R':203,'thigh_L':205,'thigh_R':205,'forearm_L':220,'forearm_R':220,
       'upper_arm_L':222,'upper_arm_R':222,'neck':239,'torso':240,'head':242,'pelvis':250}
LAYER.update(VC.get('layers',{}))   # profile views: live rig bands (arm above torso, pelvis above legs)
PARENT={'pelvis':None,'torso':'pelvis','neck':'torso','head':'neck','upper_arm_L':'torso','upper_arm_R':'torso','forearm_L':'upper_arm_L','forearm_R':'upper_arm_R',
        'thigh_L':'pelvis','thigh_R':'pelvis','shin_L':'thigh_L','shin_R':'thigh_R','foot_L':'shin_L','foot_R':'shin_R'}
def piv(old): p=rp[old]; return [p['pivotX'],p['pivotY']]
PIVOT={'pelvis':piv('pelvis'),'torso':piv('torso'),'upper_arm_L':piv('upperArm_L'),'upper_arm_R':piv('upperArm_R'),'forearm_L':piv('forearm_L'),'forearm_R':piv('forearm_R'),
       'thigh_L':piv('thigh_L'),'thigh_R':piv('thigh_R'),'shin_L':piv('shin_L'),'shin_R':piv('shin_R'),'foot_L':piv('foot_L'),'foot_R':piv('foot_R'),
       'neck':VC['neck'],'head':VC['head']} if V in ('apose','tpose') else {k:(VC[k] if k in ('neck','head') else piv({'upper_arm_L':'upperArm_L','upper_arm_R':'upperArm_R'}.get(k,k))) for k in P}
PIVSRC={k:f'views/{V}/body/rig.json' for k in PIVOT}; PIVSRC['neck']=VC['neck_src']; PIVSRC['head']=VC['head_src']
MID=VC['mid']   # hip midline
order=sorted(P,key=lambda k:(LAYER[k],k))
PARENT={k:PARENT[k] for k in P}
assert sum(P[k].sum() for k in P)==(A&~hand).sum() and not any((P[a]&P[b]).any() for a in P for b in P if a<b)
# joints: (lower-layer piece gets the flap, upper-layer piece covers it, pivot)
JOINTS={'waist':('torso','pelvis','torso'),'neck_base':('neck','torso','neck'),'head_neck':('neck','head','head'),
 'shoulder_L':('upper_arm_L','torso','upper_arm_L'),'shoulder_R':('upper_arm_R','torso','upper_arm_R'),
 'elbow_L':('forearm_L','upper_arm_L','forearm_L'),'elbow_R':('forearm_R','upper_arm_R','forearm_R'),
 'hip_L':('thigh_L','pelvis','thigh_L'),'hip_R':('thigh_R','pelvis','thigh_R'),
 'knee_L':('shin_L','thigh_L','shin_L'),'knee_R':('shin_R','thigh_R','shin_R'),
 'ankle_L':('foot_L','shin_L','foot_L'),'ankle_R':('foot_R','shin_R','foot_R')}
JOINTS={j:t for j,t in JOINTS.items() if t[0] in P and t[1] in P}
XF=VC.get('extra_flaps',{})
for j,f in XF.items(): JOINTS[j]=(f['flap_on'],f['under'],f['pivot_of'])
for j,(a_,b_,c_) in list(JOINTS.items()):   # the flap always goes on the LOWER-layer piece (profile shoulders: torso under the upper arm)
    if LAYER[a_]>LAYER[b_]: JOINTS[j]=(b_,a_,c_)
imgs={k:np.where(P[k][...,None],h,0) for k in P}
op255={k:P[k]&(h[...,3]==255) for k in P}
def nb8(m): return ndimage.binary_dilation(m,structure=np.ones((3,3)))
def rot_pts(x,y,c,th):  # rotate points (x,y) about c by th deg (canvas: + = clockwise on screen)
    t=np.radians(th); dx,dy=x-c[0],y-c[1]
    return c[0]+np.cos(t)*dx-np.sin(t)*dy, c[1]+np.sin(t)*dx+np.cos(t)*dy
FL={}; finfo={}
CAPIN={'shoulder':0.0,'elbow':0.0,'knee':0.0,'ankle':0.0,'hip':0.0}
for jn,(X,Y,pk) in JOINTS.items():
    c=np.array(PIVOT[pk],float)
    if jn in XF:   # extra cap flap (profile hips): X under Y inside a disk about Y's pivot, X and Y need not touch
        r=float(XF[jn]['radius']); disk=np.hypot(xx-c[0],yy-c[1])<=r; region=disk&op255[Y]&~P[X]
        for k2 in P:
            if k2 not in (X,Y): region&=~P[k2]
        dch=np.zeros((Hh,W))
    else:
        seam=P[X]&nb8(P[Y])
        sy,sx=np.nonzero(seam)
        S=np.stack([sx,sy],1).astype(float); m0=S.mean(0)
        w_,v_=np.linalg.eigh(np.cov((S-m0).T)); u=v_[:,1]; n=np.array([-u[1],u[0]])
        proj=(S-m0)@u; L0,L1=proj.min(),proj.max(); r=min(max((L1-L0)/2,8),70)
        # side of chord where X lives
        xy_=np.nonzero(P[X]); xc=np.array([xy_[1].mean(),xy_[0].mean()])
        if (xc-m0)@n>0: n=-n            # n points from X towards Y
        dch=(xx-m0[0])*n[0]+(yy-m0[1])*n[1]; pu=(xx-m0[0])*u[0]+(yy-m0[1])*u[1]
        # tube: X continued past the chord (geometric reflection of X's mask only; colours are flat)
        Xy,Xx=np.nonzero(P[X]); d=(Xx-m0[0])*n[0]+(Xy-m0[1])*n[1]; k=(d>-r)&(d<=0.5)
        rx=np.round(Xx[k]-2*d[k]*n[0]).astype(int); ry=np.round(Xy[k]-2*d[k]*n[1]).astype(int)
        ok=(rx>=0)&(rx<W)&(ry>=0)&(ry<Hh); tube=np.zeros((Hh,W),bool); tube[ry[ok],rx[ok]]=True
        tube=ndimage.binary_closing(tube,iterations=1)
        disk=np.hypot(xx-c[0],yy-c[1])<=r
        region=(tube|(disk&(dch>-r*0.5)&(pu>L0-4)&(pu<L1+4)))&(dch<=r)&op255[Y]&~P[X]
        for k2 in P:            # never under anything but the covering partner
            if k2 not in (X,Y): region&=~P[k2]
        LIMB=('shoulder','elbow','knee','ankle','hip')
        if jn.split('_')[0] in LIMB:
            # classic cut-out joint cap: disk about the pivot whose radius reaches the limb outline at the seam, so the
            # disk is invariant under rotation and its arc continues the outline on the opening side of the bend
            sil=~ndimage.binary_erosion(h[...,3]==255,iterations=1)
            ends=seam&ndimage.binary_dilation(sil,iterations=2)
            ey,ex_=np.nonzero(ends); dd=np.hypot(ex_-c[0],ey-c[1])
            if jn.startswith('hip'):
                lat=(ex_-MID)*(c[0]-MID)>0; dd=dd[lat&(np.abs(ex_-MID)>abs(c[0]-MID))] if (lat&(np.abs(ex_-MID)>abs(c[0]-MID))).any() else dd
            r=(float(np.max(dd)) if jn.startswith('hip') else float(np.median(dd)))-CAPIN.get(jn.split('_')[0],1.0)
            cover=op255[Y]|(op255['torso'] if jn.startswith('hip') else False)   # hips: the lateral seam end sits under the waist (torso, layer 240 > thigh 205)
            region=(np.hypot(xx-c[0],yy-c[1])<=r)&cover&~P[X]
            for k2 in P:
                if k2 not in (X,Y) and not (jn.startswith('hip') and k2=='torso'): region&=~P[k2]
            if jn.startswith('hip'):   # sweep clip, medial side only: no skin tongue below the crotch when the leg swings
                ys_,xs_=np.nonzero(region); bad=np.zeros(len(ys_),bool); med=(xs_-c[0])*(MID-c[0])>0
                for th in range(-25,26,5):
                    qx,qy=rot_pts(xs_.astype(float),ys_.astype(float),c,th)
                    qx=np.clip(np.round(qx).astype(int),0,W-1); qy=np.clip(np.round(qy).astype(int),0,Hh-1)
                    bad|=med&(h[qy,qx,3]==0)
                region[ys_[bad],xs_[bad]]=False
        elif jn=='waist':   # long curved seam: plain band under the pelvis instead of a reflected tube (cleaner flap edge)
            region=op255[Y]&(dch<=r)&~P[X]
            for k2 in P:
                if k2 not in (X,Y): region&=~P[k2]
    region=ndimage.binary_opening(region,iterations=1)|(region&nb8(P[X]))
    region=ndimage.binary_fill_holes(region|P[X])&region if jn!='waist' else region
    # exposure test over the joint range: flap px q is exposed if the covering piece does not cover it after relative rotation
    ys_,xs_=np.nonzero(region); exposed=np.zeros(len(ys_),bool)
    for th in range(-25,26,5):
        if th==0: continue
        qx,qy=rot_pts(xs_.astype(float),ys_.astype(float),c,th)
        qx=np.clip(np.round(qx).astype(int),0,W-1); qy=np.clip(np.round(qy).astype(int),0,Hh-1)
        exposed|=~(op255[Y]|(op255['torso'] if jn.startswith('hip') else False))[qy,qx]
    ex=np.zeros((Hh,W),bool); ex[ys_[exposed],xs_[exposed]]=True
    U=P[X]|region; bnd=region&~ndimage.binary_erosion(U,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    line=bnd&ex
    col=np.zeros((Hh,W,4),np.int32); col[...,:3]=SKIN; col[...,3]=255; col[line,:3]=LINE
    imgs[X][region]=col[region]
    FL.setdefault(X,np.zeros((Hh,W),bool)); FL[X]|=region
    finfo[jn]={'flap_on':X,'under':Y,'pivot':[float(c[0]),float(c[1])],'joint_radius_px':round(float(r),1),'flap_px':int(region.sum()),
               'flap_depth_px':round(float(dch[region].max()) if region.any() else 0,1),'flap_line_px':int(line.sum()),'exposed_px_in_range':int(ex.sum())}
# ---- under-hand fill (profile views): the hand lies on the thigh; Hands draw it under the forearm but it does not follow the thigh,
# so the thigh needs her flat skin inside the hand mask (only where the thigh encloses it: no new outline) ----
UH={}
for k in VC.get('underhand',[]):
    others=np.zeros_like(hand)
    for k2 in P:
        if k2!=k: others|=P[k2]|FL.get(k2,np.zeros_like(hand))
    U=ndimage.binary_fill_holes(P[k]|FL.get(k,np.zeros_like(hand))|hand)&hand&~others
    col=np.zeros((Hh,W,4),np.int32); col[...,:3]=SKIN; col[...,3]=255
    imgs[k][U]=col[U]; UH[k]=int(U.sum()); FL.setdefault(k,np.zeros((Hh,W),bool)); FL[k]|=U
# ---- write pieces ----
for k in P:
    im=imgs[k].astype(np.uint8); im[im[...,3]==0]=0
    Image.fromarray(im,'RGBA').save(f'{PD}/{k}.png')
Image.fromarray((hand*255).astype(np.uint8),'L').save(f'{OUT}/hand_mask.png')
def over(dst,src):
    sa=src[...,3:]/255.; da=dst[...,3:]/255.; oa=sa+da*(1-sa)
    rgb=np.where(oa>0,(src[...,:3]*sa+dst[...,:3]*da*(1-sa))/np.maximum(oa,1e-9),0)
    out=np.concatenate([rgb,oa*255],-1)
    e=(src[...,3:]==255)|(dst[...,3:]==0); out=np.where(e&(src[...,3:]>0),src,out); out=np.where(src[...,3:]==0,dst,out)
    return out
comp=np.zeros((Hh,W,4))
for k in order: comp=over(comp,imgs[k].astype(float))
comp=np.round(comp).astype(np.int32); comp[comp[...,3]==0]=0
ref=h.copy(); ref[hand]=0          # hands are Base Hands' layer
diff=(comp!=ref).any(-1)&~hand   # under-hand fill sits inside the hand mask (Base Hands' layer covers it)
comp_h=comp.copy(); comp_h[hand]=h[hand]; diff_h=(comp_h!=h).any(-1)
np.save('/tmp/recomp_diff.npy',diff)
parts=[]
for k in order:
    e={'id':k,'file':f'pieces/{k}.png','layer':LAYER[k],'parent':PARENT[k],'pivot':PIVOT[k],'pivotSource':PIVSRC[k],
       'pixels':int(P[k].sum()),'flapPx':int(FL.get(k,np.zeros(1,bool)).sum())}
    e['flaps']=[dict(joint=j,**{kk:vv for kk,vv in f.items() if kk!='flap_on'}) for j,f in finfo.items() if f['flap_on']==k]
    parts.append(e)
wl={}
for s in [s_ for s_ in ('L','R') if f'forearm_{s_}' in P]:
    fa=P[f'forearm_{s}']; seam=fa&nb8(hand); sy,sx=np.nonzero(seam); S=np.stack([sx,sy],1).astype(float); m0=S.mean(0)
    w_,v_=np.linalg.eigh(np.cov((S-m0).T)); u=v_[:,1]; pr=(S-m0)@u
    e1=m0+u*pr.min(); e2=m0+u*pr.max()
    wp=rp[f'forearm_{s}']['wristPivot']
    d={'view':V,'side':s,'owner':'Base Body (staged)','line':[np.round(e1,1).tolist(),np.round(e2,1).tolist()],
       'seam_px':[[int(a),int(b)] for a,b in zip(sx,sy)],'pivot':[wp['x'],wp['y']],'pivotSource':f'views/{V}/body/rig.json forearm wristPivot',
       'note':f'forearm side of the forearm/hand seam (forearm px 8-adjacent to hands/{V}_hand_erase_mask.png). Forearm piece is layered ABOVE the hand; the hand flap should tuck under the forearm past this line.',
       'mask':f'wrist_line_{s}.png'}
    json.dump(d,open(f'{OUT}/wrist_line_{s}.json','w'),indent=1); wl[s]=d
    im=Image.new('L',(W,Hh),0); dr=ImageDraw.Draw(im); dr.line([tuple(e1),tuple(e2)],fill=255,width=3)
    mm=np.array(im)>0; mm|=seam; Image.fromarray((mm*255).astype(np.uint8),'L').save(f'{OUT}/wrist_line_{s}.png')
out={'view':V,'canvas':[W,Hh],'source':f'hairless_{V}.png','coordinateSpace':'view px, every piece full canvas at x=y=0',
 'layerOrder_backToFront':order,'hands':f'not a body piece: hand_mask.png (= hands/{V}_hand_erase_mask.png); Base Hands supplies the hand layer',
 **({'hands_order':'hands are drawn UNDER the forearms (forearm 220 above the hand layer); base_body_skin.png in live_patch_staged is cut to alpha 0 inside hand_mask.png like these pieces','toes':'rig.json toes_L/R are not separate pieces: toe px are in foot_L/R (lab_tpose labels)'} if V=='tpose' else {}),
 'pieces':parts,'joints':finfo,
 **({'underhand_fill_px':UH,'underhand_note':'flat skin inside hand_mask.png on the listed pieces (hidden under the hand at rest; shows only when the thigh moves away from the hand)'} if UH else {}),
 'recomposite':{'compare':'rgba, alpha-0 px compared as transparent (hairless alpha-0 px with leftover RGB: '+str(h_a0rgb)+')','diff_px_vs_hairless_outside_hand_mask':int(diff.sum()),'diff_px_vs_hairless_with_hand_px_from_hairless':int(diff_h.sum())},
 'colours':{'skin':SKIN.tolist(),'line':LINE.tolist()}}
json.dump(out,open(f'{OUT}/parts.json','w'),indent=1)
print(json.dumps(out['recomposite']),json.dumps(finfo,indent=0))
