"""apose finger frames v2: drawn foreshortening (no scaling), childPivot per frame.
Model: palm faces the viewer, so a finger curls toward the viewer. Joint flexion (deg at curl 1) MCP/PIP/DIP = FLEX.
Each segment is drawn as a flat capsule along its rest direction with projected length L*cos(cumulative flex)
(negative -> it points back over the palm). Width is unchanged (cross-section). Outline = her 2 px line weight,
flat skin + sampled line colour, 4x supersampled. f0 = exact rest part."""
import json, os, sys, shutil, numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0,'/workspace/shadowveil/hands/work')
from defs import D
ROOT='/workspace/shadowveil'; V=sys.argv[1] if len(sys.argv)>1 else 'apose'; SS=4; W,H=1365,1739
SRC=f'{ROOT}/hands/work/backup_apose_v2' if V=='apose' else f'{ROOT}/hands/work/backup_v2/{V}'   # pre-frames delivery: rest cut + rotation-only tuning
OUT=f'{ROOT}/hands/work/frames/{V}_v2'
AWAY=V not in ('apose','tpose')
INPLANE=V=='tpose'   # side view: the curl is in the picture plane, rotation carries it; frames only replace the blocky cut pieces with clean rounded segments   # back / profiles: we see the back of the hand, fingers curl AWAY from the viewer -> folded-back pieces go behind
LW=float(os.environ.get('LW','0.88'))    # her finger line weight, calibrated by ink-width measurement (~0.7 px ink equiv.)
FLEX={'finger':(85,100,65),'thumb':(0,30,45)}
NEWCURL={'finger':(12,8,6)}               # small in-plane lean on top of the drawn foreshortening
FRAME_C=(0.5,1.0)
rig=json.load(open(f'{SRC}/rig.json')); by={p['id']:p for p in rig['parts']}
def A(pid): return np.array(Image.open(f"{SRC}/{by[pid]['file']}").convert('RGBA'))
from lw import width as _inkw
def seg_lw(path,S=None,Lc=None):
    # her line weight on this segment: ink-equivalent width of f0's outline, calibrated (drawn LW 0.88 -> ink 0.68)
    return float(np.clip(_inkw(path,S,Lc)*0.88/0.68,0.7,2.2))
def halfwidth(a):
    m=a[...,3]>0; return float(ndi.distance_transform_edt(m).max())
def capsule_mask(B,E,rb,re,box):
    x0,y0,x1,y1=box
    Y,X=np.mgrid[y0*SS:y1*SS,x0*SS:x1*SS]; Px=(X+0.5)/SS-0.5; Py=(Y+0.5)/SS-0.5
    v=E-B; L2=max(v@v,1e-9); t=np.clip(((Px-B[0])*v[0]+(Py-B[1])*v[1])/L2,0,1)
    cx=B[0]+t*v[0]; cy=B[1]+t*v[1]; r=rb+(re-rb)*t
    return (np.hypot(Px-cx,Py-cy)<=r),Px,Py
def render_shape(M,Px,Py,S,Lc,box,extra_lines=None,nolineB=None,lw=None,noline=None):
    LWs=lw or LW
    dt=ndi.distance_transform_edt(np.pad(M,4))[4:-4,4:-4]/SS
    line=M&(dt<=LWs)
    if nolineB is not None:
        # joint seam: where the child's base cap lies over the parent's (current-frame) shape, the parent's
        # outline carries the line, so the child draws no line there -> one continuous contour, no doubled ring
        B0,r0,PM,d0=nolineB; aa=(Px-B0[0])*d0[0]+(Py-B0[1])*d0[1]
        line&=~((np.hypot(Px-B0[0],Py-B0[1])<r0+LWs+0.5)&PM&(aa<0.2*r0))
    if noline is not None: line&=~noline
    if extra_lines is not None: line|=extra_lines&M
    x0,y0,x1,y1=box; h,w=y1-y0,x1-x0
    col=np.zeros(M.shape+(4,)); col[...,:3]=S; col[...,3]=M*255.0; col[line,:3]=Lc
    pm=col.copy(); pm[...,:3]*=pm[...,3:]/255
    ds=pm.reshape(h,SS,w,SS,4).mean((1,3)); al=ds[...,3:]
    rgb=np.where(al>0,ds[...,:3]/np.maximum(al,1e-6)*255,0)
    fr=np.zeros((H,W,4),np.uint8); fr[y0:y1,x0:x1,:3]=np.clip(np.round(rgb),0,255); fr[y0:y1,x0:x1,3]=np.clip(np.round(al[...,0]),0,255)
    return fr
def crease(Px,Py,C,d,r,bow=0.25):
    # short curved crease across the segment at C (1 px line at 4x = LW/2)
    n=np.array([-d[1],d[0]]); rel0=Px-C[0]; rel1=Py-C[1]
    a=rel0*d[0]+rel1*d[1]; b=rel0*n[0]+rel1*n[1]
    return (np.abs(a-bow*(b**2)/max(r,1))<=0.5)&(np.abs(b)<=r*0.6)
os.makedirs(OUT,exist_ok=True)
newrig=json.loads(json.dumps(rig)); nb={p['id']:p for p in newrig['parts']}
report={}
DONE={}
NEWMAX={}
for _p in rig['parts']:
    import re as _re
    _m=_re.match(r'^[LR]_(Index|Middle|Ring|Pinky)(\d)$',_p['id'])
    if _m: NEWMAX[_p['id']]=int(np.sign(_p['maxCurlDeg']))*[90,95,15][int(_m.group(2))-1] if INPLANE else int(np.sign(_p['maxCurlDeg']))*NEWCURL['finger'][int(_m.group(2))-1]
def behind_mask(pid,fi,k,B,Px,Py,only_parent=False):
    # union of the palm and every ancestor segment's current frame, in this segment's rest coords
    out=np.zeros(Px.shape,bool); off=np.zeros(2); cur=pid; Bc=B
    while True:
        par=by[cur]['parent']
        if par is None: break
        if par.endswith('_palm'):
            if only_parent=='fingers': break
            a=PALM.astype(float)
        else:
            fr,cp=DONE[(par,fi)]; a=(fr[...,3]>=128).astype(float); off=off+(np.array(cp)-Bc)
            Bc=np.array([by[par]['pivotX'],by[par]['pivotY']])
        out|=ndi.map_coordinates(a,[Py+off[1],Px+off[0]],order=0,cval=0)>0.5
        if par.endswith('_palm') or only_parent is True: break
        cur=par
    return ndi.binary_dilation(out,iterations=2)
def parent_mask(pid,fi,k,B,Px,Py):
    # parent's frame alpha, moved into this segment's rest coords (child base B sits on the parent's childPivot)
    if k==0: return np.zeros(Px.shape,bool)
    par=by[pid]['parent']; fr,cp=DONE[(par,fi)]
    a=ndi.binary_erosion(fr[...,3]>=160,iterations=1).astype(float)
    # the child turns by its own angle inside this frame's curl range; keep only pixels covered for every angle
    lo,hi=max(0,(fi-0.5)/2),min(1,(fi+0.5)/2); mx=abs(NEWMAX.get(pid,by[pid]['maxCurlDeg']))*np.sign(NEWMAX.get(pid,by[pid]['maxCurlDeg']) or 1)
    ok=np.ones(Px.shape,bool)
    for cc in np.linspace(lo,hi,5):
        t=np.deg2rad(cc*mx); c_,s_=np.cos(t),np.sin(t); dx,dy=Px-B[0],Py-B[1]
        rx=B[0]+c_*dx-s_*dy; ry=B[1]+s_*dx+c_*dy
        ok&=ndi.map_coordinates(a,[ry+(cp[1]-B[1]),rx+(cp[0]-B[0])],order=0,cval=0)>0.5
    return ok
for side in ('L','R'):
    Hd=rig['hands'][side]
    if not Hd.get('visible') or not by.get(f'{side}_palm',{}).get('file'): continue
    PALM=np.array(Image.open(f"{SRC}/{by[side+'_palm']['file']}").convert('RGBA'))[...,3]>=160
    if INPLANE:
        cols=np.nonzero(PALM.any(0))[0]; TOPY=np.full(W,1e9)
        for x_ in cols: TOPY[x_]=np.nonzero(PALM[:,x_])[0].min()
        # beyond the palm's end, continue its back contour flat from the last 3 columns
        lx,rx=cols.min(),cols.max(); TOPY[:lx]=TOPY[lx:lx+3].min(); TOPY[rx+1:]=TOPY[rx-2:rx+1].min()
        PALM_ER=ndi.binary_erosion(PALM,iterations=2)   # a curled finger draws no line where it lies over the palm (no fold line)
    S=np.array(Hd['skinRGB'],float); Lc=np.array(Hd['lineRGB'],float)
    x0,y0,x1,y1=Hd['box']; box=(x0-40,y0-40,x1+40,y1+40)
    for F in ['Index','Middle','Ring','Pinky','Thumb']:
        ids=[f'{side}_{F}{k}' for k in (1,2,3)]
        P=[np.array([by[i]['pivotX'],by[i]['pivotY']]) for i in ids]
        fg=D[V][side]['fingers']
        tip=np.array((fg.get(F.lower()) or fg['index'])[-1],float)   # tpose ring/pinky are stand-ins sharing the index chain
        ends=[P[1],P[2],tip]
        imgs=[A(i) for i in ids]
        hw=[halfwidth(a) for a in imgs]
        kind='thumb' if F=='Thumb' else 'finger'
        for c in FRAME_C:
            fi=int(np.floor(c*2+0.5))
            cum=0.0
            for k,pid in enumerate(ids):
                cum+=FLEX[kind][k]*c
                d=ends[k]-P[k]; L=np.linalg.norm(d); d=d/L
                ell=L if INPLANE else L*np.cos(np.deg2rad(cum))
                rb=hw[k]*(0.98 if k else 1.0)
                if F=='Thumb' and k==1: rb=max(rb,float(by[pid].get('jointRadiusPx') or 0))   # round joint cap hides the Thumb1/Thumb2 step when Thumb2 turns
                re=(hw[k+1] if k<2 else hw[k]*0.85)
                B=P[k]; E=B+d*ell
                if F=='Thumb' and k==0:
                    # metacarpal stays in the palm plane (no flexion toward the viewer): f1/f2 = rest pixels, child at rest joint
                    fr=imgs[0].copy(); cp=[float(P[1][0]),float(P[1][1])]
                else:
                    Mc,Px,Py=capsule_mask(B,E,rb,re,box)
                    s_=ell/L; n=np.array([-d[1],d[0]])
                    a=(Px-B[0])*d[0]+(Py-B[1])*d[1]; b=(Px-B[0])*n[0]+(Py-B[1])*n[1]
                    if abs(s_)>0.08 and not INPLANE:
                        sx=B[0]+(a/s_)*d[0]+b*n[0]; sy=B[1]+(a/s_)*d[1]+b*n[1]
                        Mf=ndi.map_coordinates(imgs[k][...,3].astype(float),[sy,sx],order=1,cval=0)>=128
                        # keep only the part ahead of the base (the hidden base cap stays round via the capsule)
                        Mf&=(a*np.sign(s_))>=-rb*0.2
                    else: Mf=np.zeros_like(Mc)
                    M=Mc|Mf
                    NOLINE=None
                    if INPLANE and F!='Thumb':
                        # side view: nothing of a curled finger may rise above the back contour of the hand
                        # (checked for every angle this frame shows, so the knuckles never poke out)
                        lo,hi=max(0,(fi-0.5)/2),min(1,(fi+0.5)/2); ang=NEWMAX.get(pid,by[pid]['maxCurlDeg'])
                        # world pose of this segment = product of rotations of itself and ancestors (lean ignored for childPivot shift: in-plane frames keep rest pivots)
                        chain_ids=[]; q=pid
                        while not by[q]['parent'].endswith('_palm'): q=by[q]['parent']; chain_ids.append(q)
                        chain_ids=[pid]+chain_ids
                        bad=np.zeros(Px.shape,bool)
                        for cc in np.linspace(lo,hi,5):
                            X_,Y_=Px.copy(),Py.copy()
                            for q in chain_ids:
                                t=np.deg2rad(cc*NEWMAX.get(q,by[q]['maxCurlDeg'])); c_,sn=np.cos(t),np.sin(t)
                                qx,qy=by[q]['pivotX'],by[q]['pivotY']; dx,dy=X_-qx,Y_-qy
                                X_,Y_=qx+c_*dx-sn*dy,qy+sn*dx+c_*dy
                            xi=np.clip(np.round(X_).astype(int),0,W-1)
                            bad|=(Y_<TOPY[xi]+0.5)
                            yi=np.clip(np.round(Y_).astype(int),0,H-1)
                            inp=PALM_ER[yi,xi]; NOLINE=inp if NOLINE is None else NOLINE&inp
                        M&=~bad
                    if not AWAY and not INPLANE and k>=1 and s_<0.3 and F!='Thumb':
                        # palm toward us: a segment folded back or seen end-on tucks behind the earlier segments of its
                        # finger (still in front of the palm) -> no stacked outline rings/knots
                        M&=~behind_mask(pid,fi,k,B,Px,Py,only_parent='fingers')
                    if AWAY and s_<0:
                        # folded back behind the knuckles: hide what the palm and the earlier segments cover
                        M&=~behind_mask(pid,fi,k,B,Px,Py)
                    lines=np.zeros_like(M)
                    # no interior lines at all: only her outline on flat skin
                    fr=render_shape(M,Px,Py,S,Lc,box,lines,noline=NOLINE,nolineB=(B,rb,parent_mask(pid,fi,k,B,Px,Py),d*(1 if s_>=0 else -1)),lw=seg_lw(f"{SRC}/{by[pid]['file']}",S,Lc))
                    cp=[float(E[0]),float(E[1])]
                fn=f'{pid}_f{fi}.png'; Image.fromarray(fr).save(f'{OUT}/{fn}'); DONE[(pid,fi)]=(fr,cp)
                ent=nb[pid]; ent.setdefault('_fr',{})[fi]={'file':fn,'childPivot':[round(cp[0],2),round(cp[1],2)]}
        # f0 = exact rest cut
        for pid in ids:
            shutil.copy(f"{SRC}/{by[pid]['file']}",f'{OUT}/{pid}_f0.png')
            ent=nb[pid]; fr=ent.pop('_fr')
            if pid.endswith('3'):
                for e in fr.values(): e.pop('childPivot',None)   # no child
            ent['frames']=[{'file':f'{pid}_f0.png'},fr[1],fr[2]]
            if kind=='finger' and not INPLANE:
                k=int(pid[-1])-1; old=ent['maxCurlDeg']; ent['maxCurlDegRotationOnly']=old
                ent['maxCurlDeg']=int(np.sign(old))*NEWCURL['finger'][k]
            elif not INPLANE:
                ent['maxCurlDegRotationOnly']=ent['maxCurlDeg']
newrig['frameSelect']='contract v1.2: frame = round(curl*(N-1)) = floor(curl*2+0.5) -> f0 (rest, identical to "file"), f1, f2. Frames carry "childPivot" (where the next segment attaches while that frame shows); "pivot" is never overridden (every frame is drawn from the rest pivot). No scaling: foreshortening is drawn into f1/f2.'
newrig['framesNote']=('tpose frames v2: side view, the curl stays in the picture plane and is carried by rotation (maxCurlDeg unchanged); f1/f2 replace the square-cut rest pieces with clean rounded segments of the same length and width (her line weight, flat colours), so the curled fist no longer shows blocky cut ends or the jagged ring/pinky stand-ins. Thumb keeps rotation only.') if INPLANE else V+' frames v2: f1/f2 are drawn foreshortened (curl '+('away from the viewer; folded-back pieces are hidden behind the knuckles' if AWAY else 'toward the viewer')+'). maxCurlDeg is now a small in-plane lean because the frames carry the curl; maxCurlDegRotationOnly keeps the previous rotation-only tuning for renderers that cannot show frames.'
json.dump(newrig,open(f'{OUT}/rig.json','w'),indent=1)
print('frames v2 written')
