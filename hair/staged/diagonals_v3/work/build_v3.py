# diagonals_v3 = copy of diagonals_v2 (v2 kept). 045/315: start from v2 pre-eyecut files; remove (alpha 0) hair only inside the eye OPENING
# (union of Eyes' staged diagonal white + iris(pupil inside) + lash parts, mapped with viewFit, no dilation, no gaze shift, no lid parts).
# Px v2 cut that lie outside the opening are restored only where her source turn frame (f033/f191) draws hair (blue key) at that px,
# re-snapped (hard alpha) to the live hair-art palette (views/*/hair/*.png opaque colours). Then everywhere (all 4 angles): remove iris-tone
# px (strong green anywhere; iris-part colours within 6 px of the opening) and any px off the qa_gates tol-2 palette. Writes only under hair/staged/diagonals_v3/.
from common import *
from scipy.spatial import cKDTree
import shutil
O=R+'/hair/staged/diagonals_v3'; V2=R+'/hair/staged/diagonals_v2'
art=set()
for f in glob.glob(R+'/views/*/hair/*.png'):
    a=A(f).reshape(-1,4); art|=set(map(tuple,a[a[:,3]==255][:,:3].tolist()))
AP=np.array(sorted(art)); AT=cKDTree(AP)
def iris_cols(ang):
    c=set()
    for f in glob.glob(f'{R}/eyes/staged/diagonals/{ang}/Eye?_iris.png'):
        a=A(f).reshape(-1,4); c|=set(map(tuple,a[a[:,3]>0][:,:3].tolist()))
    return np.array(sorted(c))
IC=np.concatenate([iris_cols('045'),iris_cols('315')]); IT=cKDTree(IC)
from scipy import ndimage as nd
def iris_tone(rgb,near=None):
    # strong green anywhere; iris-part colour match (<=3, not a live hair-art colour) only near the eye (opening dilated 6 px)
    d,_=IT.query(rgb); da,_=AT.query(rgb); g=rgb[:,1]-np.maximum(rgb[:,0],rgb[:,2])
    nr=np.zeros(len(rgb),bool) if near is None else near
    return ((d<=3)&(da>0)&nr)|((g>=15)&(rgb[:,1]>=50))
res={}
for ang in ('045','135','225','315'):
    r={}; op=opening(ang) if ang in FR else np.zeros((H,W),bool); NEAR=nd.binary_dilation(op,iterations=6)
    if ang in FR:
        Image.fromarray((op*255).astype(np.uint8)).save(f'{O}/{ang}/eye_opening_view.png')
        sv=src_view(ang); key=(sv[...,3]>0)&(sv[...,2]-np.maximum(sv[...,0],sv[...,1])>60)
        Image.fromarray((key*255).astype(np.uint8)).save(f'{O}/{ang}/src_hair_key_view.png')
    for f in sorted(glob.glob(f'{O}/{ang}/hair/*.png')):
        n=os.path.basename(f); a=A(f); e={}
        if ang in FR:
            pre=A(f'{V2}/pre_eyecut/{ang}/hair/{n}') if os.path.exists(f'{V2}/pre_eyecut/{ang}/hair/{n}') else A(f'{V2}/pre_eyecut/{ang}/{n}')
            cut=(pre[...,3]>0)&(a[...,3]==0)
            cand=cut&~op
            irs=np.zeros((H,W),bool); ys,xs=np.nonzero(cand)
            if len(ys): irs[ys,xs]=iris_tone(pre[ys,xs,:3],NEAR[ys,xs])
            rest=cand&key&~irs
            ys,xs=np.nonzero(rest)
            if len(ys):
                d,i=AT.query(pre[ys,xs,:3]); a[ys,xs,:3]=AP[i]; a[ys,xs,3]=255; e['restore_snapped_px']=int((d>0).sum()); e['restore_max_snap']=round(float(d.max()),1)
            # anything (old or restored) inside the opening -> 0
            inop=(a[...,3]>0)&op; a[inop]=0
            e.update(v2_cut_px=int(cut.sum()),restored_over_lid=int(rest.sum()),still_removed_in_opening=int((cut&op).sum()),
                     not_restored_outside_opening_no_src_hair=int((cand&~key&~irs).sum()),not_restored_iris_tone=int((cand&irs).sum()),
                     extra_removed_in_opening=int(inop.sum()))
        # iris tone anywhere
        m=a[...,3]>0; ys,xs=np.nonzero(m); it=iris_tone(a[ys,xs,:3],NEAR[ys,xs]) if len(ys) else np.zeros(0,bool)
        a[ys[it],xs[it]]=0; e['iris_tone_removed']=int(it.sum())
        Image.fromarray(a.astype(np.uint8),'RGBA').save(f); r[n]=e
    res[ang]=r
json.dump(res,open(f'{O}/build_v3.json','w'),indent=1)
for ang,r in res.items():
    for n,e in r.items():
        if any(v for k,v in e.items()): print(ang,n,e)
