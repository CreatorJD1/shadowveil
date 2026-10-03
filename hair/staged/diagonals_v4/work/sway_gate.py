# Sway gate for diagonals_v4 (045/315, view + frame scale). Python mirror of rig/index.html hair transform (slider + per-segment drive):
#   angle_p = x_p>=0 ? x_p*degAtPlus1 : |x_p|*degAtMinus1   (defaults: +-swayWeight*maxSwayDeg; page today = swayWeight*maxSwayDeg*x)
#   M_p = M_parent . rotAt(pivotX,pivotY,angle_p) (chain, rotAt as index.html: [c,s,-s,c,px-c*px+s*py,py-s*px-c*py]); final = T(0,dy).M_p,
#   dy = round(clamp(y)*swayY*swayYMaxPx). Head group is common to eyes, mouth and hair, so it cancels. Nearest inverse sampling.
# Counts front hair px (layer>=200; hair_back/bun are behind the body) over: eye opening = Eyes' white + iris (iris swept over its gaze limits),
# mouth = interior+lip+line classes of every Mouth diag_posable shape (frame/view) + diag rest lips mask. Segment drives x_p swept independently.
import sys,glob,json,os,itertools,numpy as np
sys.path.insert(0,'/workspace/shadowveil/hair/staged/diagonals_v3/work')
from common import A,R,W,H
from PIL import Image
from scipy import ndimage as nd
O=R+'/hair/staged/diagonals_v4'; D=json.load(open(R+'/body_tools/work/apose_turn/diagonals/diagonals.json'))['diagonals']
XS=np.linspace(-1,1,21); YS=[-1,-.5,0,.5,1]
def rot(px,py,deg):
    if deg==0: return np.eye(3)
    t=np.radians(deg); c,s=np.cos(t),np.sin(t); return np.array([[c,-s,px-c*px+s*py],[s,c,py-s*px-c*py],[0,0,1]])
def masks(ang,scale):
    vf=D[ang.lstrip('0')]['view_fit']; s,dx,dy=vf['scale'],vf['dx'],vf['dy']; E=f'{R}/eyes/staged/diagonals/{ang}'
    rig=json.load(open(f'{E}/rig.json')); lim=rig.get('irisLimitsPx',{})
    op=np.zeros((1168,768),bool)
    for eye in ('EyeL','EyeR'):
        w=A(f'{E}/{eye}_white.png')[...,3]>0; ir=A(f'{E}/{eye}_iris.png')[...,3]>0; op|=w
        L=lim.get(eye,{}); 
        for ddx in range(L.get('dxAtXminus1',-2),L.get('dxAtXplus1',2)+1):
            for ddy in range(L.get('dyAtYminus1',-1),L.get('dyAtYplus1',1)+1): op|=np.roll(np.roll(ir,ddy,0),ddx,1)
    M=f'{R}/mouth/staged/diag_posable/{ang}'
    yy,xx=np.mgrid[0:H,0:W]; fx=np.floor((xx+.5-dx)/s).astype(int); fy=np.floor((yy+.5-dy)/s).astype(int); ok=(fx>=0)&(fx<768)&(fy>=0)&(fy<1168)
    fyy,fxx=np.mgrid[0:1168,0:768]; vx=np.clip(np.floor(s*(fxx+.5)+dx).astype(int),0,W-1); vy=np.clip(np.floor(s*(fyy+.5)+dy).astype(int),0,H-1)
    # mouth (Mouth's staged diag_posable): rest = alpha of rest.png (frame_scale/rest.png in frame px; view: rest.png alpha | diag rest lips mask);
    # every open shape (M, smile, OH/AA/EE + halves) = its own alpha, checked separately at full sway
    rl=np.array(Image.open(f'{R}/mouth/staged/diagonals/diag_{ang}_rest_mask.png'))>0
    sub=f'{M}/frame_scale' if scale=='frame' else M
    tg={}
    for g in sorted(glob.glob(f'{sub}/*.png')):
        n=os.path.basename(g)[:-4]; tg['mouth' if n=='rest' else 'shape:'+n]=A(g)[...,3]>0
    if scale=='view': tg['mouth']=tg.get('mouth',np.zeros((H,W),bool))|rl
    if scale=='frame': return op,tg
    opv=np.zeros((H,W),bool); opv[ok]=op[fy[ok],fx[ok]]
    return opv,tg
def load(ang,scale):
    d=f'{O}/{ang}/hair' if scale=='view' else f'{O}/{ang}/frame_scale/hair'
    rig=json.load(open(f'{d}/rig.json')); parts=[p for p in rig['parts']]
    im={p['id']:A(f"{d}/{p['file']}")[...,3]>0 for p in parts}
    return d,rig,parts,im
def count(parts,im,ymax,xd,y,targets):
    by={p['id']:p for p in parts}; Mm={}
    def m(i):
        if i in Mm: return Mm[i]
        p=by[i]; x=xd.get(i,0.0)
        up=p.get('degAtPlus1',(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)); dn=p.get('degAtMinus1',-(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0))
        a=x*up if x>=0 else abs(x)*dn
        base=m(p['parent']) if p.get('parent') in by else np.eye(3)
        Mm[i]=base@rot(p['pivotX'],p['pivotY'],a); return Mm[i]
    out={k:{} for k in targets}
    for p in parts:
        if p['layer']<200 or not im[p['id']].any(): continue
        dyp=int(np.round(np.clip(y,-1,1)*min(max(p.get('swayY') or 0,0),1)*ymax)) if y else 0
        Mi=np.linalg.inv(np.array([[1,0,0],[0,1,dyp],[0,0,1]])@m(p['id'])); a=im[p['id']]; hh,ww=a.shape
        for k,(ys,xs) in targets.items():
            sx=Mi[0,0]*(xs+.5)+Mi[0,1]*(ys+.5)+Mi[0,2]; sy=Mi[1,0]*(xs+.5)+Mi[1,1]*(ys+.5)+Mi[1,2]
            ix=np.floor(sx).astype(int); iy=np.floor(sy).astype(int); okk=(ix>=0)&(ix<ww)&(iy>=0)&(iy<hh)
            n=int(a[iy[okk],ix[okk]].sum())
            if n: out[k][p['id']]=n
    return out
def drives(parts):
    sw=[p['id'] for p in parts if (p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)]
    # roots/tips: independent drive per swaying segment would be 21^n; sweep chains pairwise (each chain independent, others at the same x)
    by={p['id']:p for p in parts}; chains={}
    for i in sw:
        r=i
        while by[r].get('parent') in by and by[by[r]['parent']].get('swayWeight'): r=by[r]['parent']
        chains.setdefault(r,[]).append(i)
    return sw,chains
def sweep(parts,im,ymax,targets):
    sw,chains=drives(parts); worst={k:(0,None) for k in targets}; per={}
    for X in XS:                                  # slider path: one x for every segment
        for y in YS:
            o=count(parts,im,ymax,{i:X for i in sw},y,targets)
            for k in targets:
                t=sum(o[k].values())
                for pid,n in o[k].items(): per[(k,pid,'+' if X>0 else '-')]=max(per.get((k,pid,'+' if X>0 else '-'),0),n)
                if t>worst[k][0]: worst[k]=(t,dict(X=round(float(X),2),Y=y,parts=o[k],path='slider'))
    for r,segs in chains.items():                 # per-segment drive (sim path): each segment of a chain independent in -1..1
        if len(segs)<2: continue
        for xs in itertools.product(XS[::2],repeat=len(segs)):
            for y in (-1,0,1):
                o=count(parts,im,ymax,dict(zip(segs,xs)),y,targets)
                for k in targets:
                    t=sum(o[k].values())
                    for pid,n in o[k].items():
                        sg='+' if xs[segs.index(pid)]>0 else '-' if pid in segs else '?'
                        per[(k,pid,sg)]=max(per.get((k,pid,sg),0),n)
                    if t>worst[k][0]: worst[k]=(t,dict(x=dict(zip(segs,[round(float(v),2) for v in xs])),Y=y,parts=o[k],path='segments'))
    return worst,per
if __name__=='__main__':
    res={}
    for ang in ('045','315'):
        for scale in ('view','frame'):
            d,rig,parts,im=load(ang,scale); op,mt=masks(ang,scale)
            tg={'eye_opening':np.nonzero(op)}|{k:np.nonzero(v) for k,v in mt.items()}
            worst,per=sweep(parts,im,rig.get('swayYMaxPx',3),tg)
            res[f'{ang}_{scale}']=dict(opening_px=int(op.sum()),mouth_px={k:int(v.sum()) for k,v in mt.items()},worst={k:dict(px=v[0],state=v[1]) for k,v in worst.items()},
                                       per_part_dir={f'{k}|{p}|{s}':n for (k,p,s),n in per.items() if n})
            print(ang,scale,json.dumps(res[f'{ang}_{scale}']),flush=True)
    json.dump(res,open(sys.argv[1] if len(sys.argv)>1 else f'{O}/sway_gate_before.json','w'),indent=1)
