# diagonals_v4 = copy of diagonals_v3 (v3 kept). Writes only under hair/staged/diagonals_v4/. Read-only on reference/, eyes/, mouth/, body_tools/, views/.
# HER HAIR (frame coords) = (eye zone: dark untinted lash/lid ink near Eyes' parts is not hair)  Hair's v1 frame hair segmentation (key.hair_mask, enclosed key loops keyed, as build.py) with key-unmix alpha >= 0.5
#   and not key-blue by the qa_gates chroma rule; minus Eyes' white+iris (frame-coord parts; lash allowed, Eyes trims lash) and the mouth lips mask.
# view scale: fill hair_mask_view px whose nearest frame px (viewFit floor map) is HER HAIR and that v3 leaves uncovered; part = the v1 part with
#   the highest soft alpha there; colour = v1 colour snapped to that part's live hair-art palette (views/*/hair/<part>.png opaque; all hair art if the part is not live).
# frame scale: <ang>/frame_scale/hair/*.png, 768x1168, = exact copies of her frame px on HER HAIR (native cut, no resampling), part label from the v4 view part
#   at the px centre (nearest labelled if none); rig.json in frame coords.
import sys,os,glob,json,numpy as np
sys.path.insert(0,'/workspace/shadowveil/hair/staged/diagonals/work')
from toview import hair_rgba_raw,D
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial import cKDTree
R='/workspace/shadowveil'; O=R+'/hair/staged/diagonals_v4'; W,H=1365,1739
A=lambda p:np.array(Image.open(p).convert('RGBA')).astype(int)
sys.path.insert(0,R+'/body_tools/work/apose_turn'); from seg import mask_of
FRA={'045':33,'135':87,'225':131,'315':191}; DK={'045':'45','135':'135','225':'225','315':'315'}
def chroma(c): return (c[...,2]>np.maximum(c[...,0],c[...,1])+60)&(c[...,2]>120)
artp={}; allart=set()
for f in glob.glob(R+'/views/*/hair/*.png'):
    a=A(f).reshape(-1,4); s=set(map(tuple,a[a[:,3]==255][:,:3].tolist())); n=os.path.basename(f); artp[n]=artp.get(n,set())|s; allart|=s
def pal(n):
    P=np.array(sorted(artp.get(n,allart))); return P,cKDTree(P)
res={}
for ang,f in FRA.items():
    vf=D[DK[ang]]['view_fit']; s,dx,dy=vf['scale'],vf['dx'],vf['dy']
    rgb,hair,al,Fc,d=hair_rgba_raw(f); fh,fw=al.shape
    ex_raw=rgb.astype(int)[...,2]-np.maximum(rgb[...,0],rgb[...,1]).astype(int)
    segm=mask_of(f'{R}/reference/apose_turn/frames/f{f:03d}.png'); ys_,_=np.nonzero(segm); t_,b_=ys_.min(),ys_.max()
    hz22=np.zeros_like(segm); hz22[t_:int(t_+.22*(b_-t_))]=True; hullk=segm&(ex_raw>120)&hz22; al=al.copy(); al[hullk]=0
    her=(al>=0.5); keyblue=her&chroma(rgb.astype(int)); her&=~keyblue
    # frame<->view maps
    yy,xx=np.mgrid[0:H,0:W]; fx=np.floor((xx+0.5-dx)/s).astype(int); fy=np.floor((yy+0.5-dy)/s).astype(int); okv=(fx>=0)&(fx<fw)&(fy>=0)&(fy<fh)
    def f2v(m):
        o=np.zeros((H,W),bool); o[okv]=m[fy[okv],fx[okv]]; return o
    fyy,fxx=np.mgrid[0:fh,0:fw]; vx=np.clip(np.floor(s*(fxx+0.5)+dx).astype(int),0,W-1); vy=np.clip(np.floor(s*(fyy+0.5)+dy).astype(int),0,H-1)
    excl_f=np.zeros((fh,fw),bool); lash_f=np.zeros((fh,fw),bool); mouth_v=np.zeros((H,W),bool)
    E=f'{R}/eyes/staged/diagonals/{ang}'; ez=np.zeros((fh,fw),bool)
    if os.path.isdir(E):
        for p in ('white','iris'):
            for g in glob.glob(f'{E}/Eye?_{p}.png'): excl_f|=A(g)[...,3]>0
        for g in glob.glob(f'{E}/Eye?_lash.png'): lash_f|=A(g)[...,3]>0
    mp=f'{R}/mouth/staged/diagonals/diag_{ang}_rest_mask.png'
    if os.path.exists(mp): mouth_v=nd.binary_dilation(np.array(Image.open(mp))>0)
    excl_f|=mouth_v[vy,vx]
    # eye zone (all Eyes' parts dilated 8 frame px): dark px that are not navy/key-tinted (blue excess <= 10) are her lash / lid ink, not hair
    ep=np.zeros((fh,fw),bool)
    for g in glob.glob(f'{E}/Eye?_*.png'):
        if 'chroma' not in g: ep|=A(g)[...,3]>0
    ez=nd.binary_dilation(ep,iterations=8)&(ex_raw<=10)&~excl_f; lash_ink_px=int((her&ez).sum()); excl_f|=ez
    trim=np.zeros((fh,fw),bool); TB=f'{R}/eyes/staged/diagonals/backups_lash_hair_trim/{ang}'
    for g in glob.glob(f'{TB}/Eye?_lash.png'):
        cur=f'{E}/'+os.path.basename(g); trim|=(A(g)[...,3]>0)&(A(cur)[...,3]==0)
    trim&=~excl_f
    ez_all=ez; her_hair_over_excl=int((her&excl_f&~ez).sum()); her&=~excl_f; her_raw=her.copy(); her|=trim
    strict_v=f2v(excl_f&~ez_all)|mouth_v; excl_v=f2v(excl_f)|mouth_v
    # ---------- view scale ----------
    mv=np.array(Image.open(f'{R}/hair/staged/diagonals/{ang}/hair_mask_view.png'))>127
    names=sorted(os.path.basename(g) for g in glob.glob(f'{O}/{ang}/hair/*.png'))
    V3={n:A(f'{O}/{ang}/hair/{n}') for n in names}; V1={n:A(f'{R}/hair/staged/diagonals/{ang}/hair/{n}') for n in names}
    ezv=f2v(ez_all); cleared={}
    for n,a in V3.items():
        m=(a[...,3]>0)&ezv; cleared[n]=int(m.sum()); a[m]=0
    cov3=np.zeros((H,W),bool)
    for a in V3.values(): cov3|=a[...,3]>0
    trim_v=f2v(trim); T=((mv&f2v(her))|trim_v)&~excl_v; add=T&~cov3
    st=np.stack([V1[n][...,3] for n in names]); best=st.argmax(0)
    r={}; lab=np.full((H,W),-1)
    for i,n in enumerate(names):
        a=V3[n]; m=add&(best==i)&(st[i]>0); ys,xs=np.nonzero(m)
        if len(ys):
            P,Tr=pal(n); dd,ii=Tr.query(V1[n][ys,xs,:3]); a[ys,xs,:3]=P[ii]; a[ys,xs,3]=255
        lash_v=f2v(lash_f&~excl_f)
        r[n]=dict(cleared_over_eye_zone_ink=cleared[n],added=int(m.sum()),added_over_lash=int((m&lash_v).sum()))
        Image.fromarray(a.astype(np.uint8),'RGBA').save(f'{O}/{ang}/hair/{n}'); lab[a[...,3]>0]=i
    cov4=lab>=0; noadd=int((add&~cov4).sum())
    vs=dict(hair_mask_px=int(mv.sum()),uncovered_mask_v3=int((mv&~cov3).sum())-sum(cleared.values()),uncovered_mask_v4=int((mv&~cov4).sum()),
            her_hair_view_px=int(T.sum()),uncovered_her_hair_v3=int((T&~cov3).sum()),uncovered_her_hair_v4=int((T&~cov4).sum()),
            added=int(add.sum()),added_outside_mask=int((cov4&~cov3&~mv).sum()),added_outside_her_hair=int((cov4&~cov3&~T).sum()),
            left_out_mask_px_not_her_hair=int((mv&~cov4&~T).sum()),hair_over_white_iris_or_mouth=int((cov4&strict_v).sum()),hair_over_eye_zone_ink=int((cov4&ezv).sum()),cleared_over_eye_zone_ink=sum(cleared.values()),
            added_over_lash=sum(x['added_over_lash'] for x in r.values()),add_unassigned=noadd,eyes_lash_trim_view_px=int(trim_v.sum()),trim_view_hole=int((trim_v&~cov4).sum()),trim_view_outside_mask=int((trim_v&~mv).sum()),parts=r)
    # ---------- frame scale ----------
    FS=f'{O}/{ang}/frame_scale/hair'; os.makedirs(FS,exist_ok=True)
    flab=lab[vy,vx]
    if (her&(flab<0)).any():
        idx=nd.distance_transform_edt(lab<0,return_distances=False,return_indices=True); flab=np.where(flab<0,lab[idx[0],idx[1]][vy,vx],flab)
    fr={}; comp=np.zeros((fh,fw,4),int); cnt=np.zeros((fh,fw),int)
    for i,n in enumerate(names):
        m=her&(flab==i); img=np.zeros((fh,fw,4),np.uint8); img[m,:3]=rgb[m]; img[m,3]=255
        mt=m&trim&~her_raw
        if mt.any():
            P,Tr=pal(n); dd,ii=Tr.query(Fc[mt]); img[mt,:3]=P[ii]
        Image.fromarray(img,'RGBA').save(f'{FS}/{n}'); fr[n]=int(m.sum()); comp[m]=img[m]; cnt+=m
    rest_diff=int(((comp[...,3]>0)!=her).sum()+((np.abs(comp[...,:3]-rgb.astype(int)).max(-1)>0)&her_raw).sum())
    # rig.json in frame coords from the v4 view rig
    vr=json.load(open(f'{O}/{ang}/hair/rig.json')); parts=[]
    for p in vr['parts']:
        q=dict(p); q['pivotX']=round((p['pivotX']-dx)/s,2); q['pivotY']=round((p['pivotY']-dy)/s,2); q['px']=fr.get(p['file'],0)
        if p.get('parent') is None: q['parentGroup']='head'
        parts.append(q)
    hp=(681.5,318)
    frig=dict(view=f'diagonal_{ang}',frame=f'f{f:03d}',source=f'reference/apose_turn/frames/f{f:03d}.png',canvas=[fw,fh],
              units='FRAME px of the turn frame, origin top-left; parts full-canvas (x=y=0) in drawn position. Map to view space with viewFit.',
              viewFit=dict(scale=s,dx=dx,dy=dy,rule='base_x = scale*frame_x + dx; base_y = scale*frame_y + dy'),
              headGroup=dict(note='root hair parts (parent null) are carried by the head bone / HEAD GROUP, as in views/*/hair/rig.json',
                             pivot_view=list(hp),pivot_frame=[round((hp[0]-dx)/s,2),round((hp[1]-dy)/s,2)]),
              swayYMaxPx=round(vr.get('swayYMaxPx',3)/s,2),swayYMaxPx_note='view value 3 px / scale',
              springBones=[p['id'] for p in parts if p.get('swayWeight')],parts=parts)
    json.dump(frig,open(f'{FS}/rig.json','w'),indent=1)
    fs=dict(her_hair_px=int(her.sum()),parts=fr,overlap_px=int((cnt>1).sum()),rest_composite_vs_her_frame_hair_px=rest_diff,
            keyblue_hair_px_excluded=int(keyblue.sum()),eyes_lash_trim_px=int(trim.sum()),trim_px_covered=int((trim&(comp[...,3]>0)).sum()),trim_px_hole=int((trim&~(comp[...,3]>0)).sum()),her_hair_px_over_white_iris_mouth_excluded=her_hair_over_excl,lash_px_with_hair=int((her&lash_f).sum()),eye_zone_lash_ink_px_excluded=lash_ink_px)
    res[ang]=dict(frame=f'f{f:03d}',view_scale=vs,frame_scale=fs); print(ang,json.dumps({k:v for k,v in vs.items() if k!='parts'}),json.dumps({k:v for k,v in fs.items() if k!='parts'}),flush=True)
json.dump(res,open(f'{O}/build_v4.json','w'),indent=1)
