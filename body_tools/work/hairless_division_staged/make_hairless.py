# Base Body staged: hairless base per view (apose, tpose, left, right, back). Writes ONLY under body_tools/work/hairless_division_staged/<view>/.
# Per-view geometry in <view>/view_config.json (absent -> the A-pose values below).
import json, glob, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT='/workspace/shadowveil'; V=sys.argv[1] if len(sys.argv)>1 else 'apose'
OUT=f'{ROOT}/body_tools/work/hairless_division_staged/{V}'; os.makedirs(OUT,exist_ok=True)
CFG=json.load(open(f'{OUT}/view_config.json')) if os.path.exists(f'{OUT}/view_config.json') else {}
base=np.array(Image.open(f'{ROOT}/views/{V}/base.png')).astype(np.int32); Hh,W=base.shape[:2]
SRC=CFG.get('source')   # e.g. body_tools/work/hairless_division_staged/tpose/live_patch_staged/base_body.png (speck-cleared body); default = base.png
b=np.array(Image.open(f'{ROOT}/{SRC}').convert('RGBA')).astype(np.int32) if SRC else base.copy()
b_raw=b.copy()   # exact source bytes (incl. RGB of transparent px)
b[b[...,3]==0]=0
A=b[...,3]>0
EAR_TOP=CFG.get('ear_top',216)
KEEP=np.zeros(b.shape[:2],bool)   # ink Hair has not cut yet (e.g. T-pose eye-corner strands): never in the hair mask, never cleaned
for kx0,ky0,kx1,ky1 in CFG.get('keep_boxes',[]): KEEP[ky0:ky1+1,kx0:kx1+1]=True
def m(p): a=np.array(Image.open(p)); return (a[...,-1] if a.ndim==3 else a)>127
INK=np.zeros(b.shape[:2],bool); ink_list=[]
if CFG.get('other_views_ink'):
    # px of hair/staged/ear_strands/work/other_views.json (same definition as Hair's other_views.py, on the LIVE base_body + Hair's rest mask):
    # kept as drawn unless Hair cut it into a staged hair part of this view (checked below, after STAGED is known)
    bb_=np.array(Image.open(f'{ROOT}/views/{V}/base_body.png').convert('RGBA')).astype(int)
    rest_=np.array(Image.open(f'{ROOT}/hair/handoff_hairless/{V}_hair_rest_mask.png'))>0
    rest_=rest_ if rest_.ndim==2 else rest_[...,-1]
    head_=np.zeros(rest_.shape,bool); head_[:330]=True
    near_=ndimage.binary_dilation(rest_,iterations=2)&~rest_&head_
    al_=bb_[...,3]; dark_=(bb_[...,:3].max(-1)<90)&(al_>=200); thick_=ndimage.binary_opening(dark_,np.ones((3,3)))
    l_,n_=ndimage.label(thick_&head_&~rest_,np.ones((3,3)))
    for i in range(1,n_+1):
        q=l_==i
        if q.sum()>=12 and (q&near_).any(): INK|=q; ink_list.append(('thick',q))
    opq_=ndimage.binary_dilation(al_>=200,np.array([[0,1,0],[1,1,1],[0,1,0]]))
    faint_=(al_>0)&(al_<=80)&(bb_[...,:3].max(-1)<90)&~opq_&~rest_&ndimage.binary_dilation(rest_,iterations=12)&head_
    l_,n_=ndimage.label(faint_,np.ones((3,3)))
    for i in range(1,n_+1):
        q=l_==i
        if q.sum()>=3: INK|=q; ink_list.append(('faint',q))
# --- hair mask ---
Hp=np.zeros((Hh,W),bool)
for f in glob.glob(f'{ROOT}/views/{V}/hair/*.png'):
    p=np.array(Image.open(f)).astype(np.int32); Hp|=(p[...,3]>0)&(p==base).all(-1)   # visible hair = part px copied from base
STAGED=np.zeros_like(Hp)   # any px Hair has put into a STAGED hair part of this view (left/right/back: speck_fix + lineart_fix)
for d_ in CFG.get('staged_hair_dirs',[]):
    for f in sorted(glob.glob(f'{ROOT}/{d_}/*.png')):
        p=np.array(Image.open(f).convert('RGBA')).astype(np.int32); STAGED|=p[...,3]>0; Hp|=(p[...,3]>0)&(p==base).all(-1)
erase=m(f'{ROOT}/hair/{V}_hair_erase_mask.png')
INK&=A   # only ink still present in the speck-cleared source
INK_cut=INK&STAGED; INK_keep=INK&~STAGED; KEEP|=INK_keep; Hp|=INK_cut
S=np.zeros_like(Hp)
sp=json.load(open(f'{ROOT}/hair/staged/speck_fix/for_base_body/speck_px.json')).get(V,{}).get('pixels',[])
for q in sp: S[q['y'],q['x']]=True
handoff=f'{ROOT}/hair/handoff_hairless'; sweep=None
for cand in glob.glob(f'{handoff}/{V}*sweep*.png'): sweep=m(cand)
# residual hair: alpha>0 head-zone pixels not in any hair part, disconnected from the face/neck body and from the ears
zy,zx0,zx1=CFG.get('resid_zone',[352,540,830]); zone=np.zeros_like(Hp); zone[:zy,zx0:zx1]=True
R=A&~Hp&~S
if CFG.get('resid_excludes_keep'): R&=~KEEP   # profile/back: kept (listed) ink must not chain loose hair wisps to the body
lab,k=ndimage.label(R&zone,structure=np.ones((3,3)))
sz=ndimage.sum(np.ones_like(R),lab,range(1,k+1)); big=int(np.argmax(sz))+1
rgb=b[...,:3]; skincls=(b[...,3]==255)&(rgb[...,0]>140)&(rgb[...,2]<120)&(rgb[...,0]-rgb[...,2]>60)
skf=ndimage.mean(skincls,lab,range(1,k+1))
ears=np.isin(lab,[i+1 for i in range(k) if i+1!=big and skf[i]>=0.2])  # skin islands (ears, forehead/temple skin between strands) are body
for ex0,ey0,ex1,ey1 in CFG.get('ear_boxes',[]):   # ear art cut off from the face by a transparent gap (T-pose image-right ear): body, not residual hair
    for i,sl in enumerate(ndimage.find_objects(lab)):
        if sl and i+1!=big and sl[1].start>=ex0 and sl[1].stop-1<=ex1 and sl[0].start>=ey0 and sl[0].stop-1<=ey1: ears|=lab==i+1
resid=(lab>0)&(lab!=big)&~ears
F=lab==big
dH=ndimage.distance_transform_edt(~(Hp|S))
lum=rgb.mean(-1)
skin_med=np.median(b[F&skincls&(np.mgrid[0:Hh,0:W][0]<CFG.get('skin_sample_ymax',200))][:,:3],0)
cd=np.abs(rgb-skin_med).sum(-1)
fr=json.load(open(f'{OUT}/cranium.json'))['fringe']
fringe=F&(np.mgrid[0:Hh,0:W][0]<fr['ymax'])&(dH<=fr['dist'])&(cd>fr['coldiff'])
# --- locks ---
locks={}
if os.path.exists(f'{ROOT}/eyes/handoff_hairless/{V}_eye_brow_lock.png'): locks['eye_brow']=m(f'{ROOT}/eyes/handoff_hairless/{V}_eye_brow_lock.png')
if os.path.exists(f'{ROOT}/mouth/handoff_hairless/{V}_mouth_lock.png'): locks['mouth']=m(f'{ROOT}/mouth/handoff_hairless/{V}_mouth_lock.png')
locks['hand']=m(f'{ROOT}/hands/{V}_hand_erase_mask.png')
# own face lock: nose + beauty mark + every non-hair pixel of the face oval (brow line to chin, between the cheek outlines)
fringe&=np.mgrid[0:Hh,0:W][0]<EAR_TOP   # below the ear tops (ear/side-head junction, ear strand ink) nothing changes vs the previous run
fy1,fx0,fx1=CFG.get('face_box',[320,600,770]); face=np.zeros_like(Hp); face[EAR_TOP:fy1,fx0:fx1]=True; face&=F&~fringe   # own face lock now starts below the forehead/temples (new eye/brow lock covers only eyes+brows)
dark=(A)&(rgb.mean(-1)<120)
own=np.zeros_like(Hp); own[150:320,600:770]=True
ny0,ny1,nx0,nx1=CFG.get('nose_box',[225,270,665,700]); nose=np.zeros_like(Hp); nose[ny0:ny1,nx0:nx1]=True; nose&=~(Hp|S|erase)
beauty=np.zeros_like(Hp)
for by0,by1,bx0,bx1 in CFG.get('beauty_boxes',[[235,262,605,650],[235,262,715,755]]): beauty[by0:by1,bx0:bx1]=True
beauty&=~(Hp|S|erase)
locks['nose']=nose; locks['beauty_marks']=beauty; locks['face_oval_nonhair']=face
for nm_,(y0_,y1_,x0_,x1_) in CFG.get('extra_locks',{}).items():   # profile line, ears, ... : every non-hair px in the box
    q=np.zeros_like(Hp); q[y0_:y1_,x0_:x1_]=True; locks[nm_]=q&A&~(Hp|S)&~KEEP
anylock=np.zeros_like(Hp)
for L in locks.values(): anylock|=L
resid&=~anylock&~KEEP
fringe&=~anylock&~KEEP
M=Hp|S|resid|erase|fringe
for k_,L in locks.items():
    if (L&M).any(): print('WARN lock overlaps hair mask',k_,int((L&M).sum()))
# --- cranium ---
yy,xx=np.mgrid[0:Hh,0:W]
_el=json.load(open(f'{OUT}/cranium.json')).get('ellipse')
if _el:
    cx,cy,ax,by=[float(x) for x in _el]
    E=(((xx-cx)/ax)**2+((yy-cy)/by)**2<=1)&(yy<=cy)
else: E=np.zeros_like(Hp); cx=cy=ax=by=0.0
Ef=json.load(open(f'{ROOT}/body_tools/ear_line_fill.json')); lrgb=np.array(Ef['rgb'])
EL=np.zeros_like(Hp)
for x,y in (Ef.get(V,[]) if CFG.get('ear_line_fill',True) else []): EL[y,x]=True   # back hairless: off (the restored lobe/jaw outline would hang below the lobes once the hair is gone)
EL_dropped=0
if CFG.get('ear_line_fill_attached_only'):   # hairless: a restored outline px floating off the ear/face (hidden under hair in the haired rig) would be a speck
    elab,_=ndimage.label(EL|F|ears,structure=np.ones((3,3))); keep_l=elab[F].max() if F.any() else 0
    bodyl=set(np.unique(elab[F|ears]))-{0}
    fl=EL&~np.isin(elab,[l for l in bodyl if (elab==l).sum()>=100]); EL_dropped=int(fl.sum()); EL&=~fl
CR=json.load(open(f'{OUT}/cranium.json'))
from PIL import ImageDraw
def poly(pts):
    im=Image.new('L',(W,Hh),0); ImageDraw.Draw(im).polygon([tuple(map(float,p)) for p in pts],fill=255,outline=255); return np.array(im)>0
from scipy.spatial import ConvexHull
HA=CFG.get('ear_hull_min_alpha',0)   # T-pose: faint (alpha<128) tail under the image-right lobe must not stretch the ear hull
hull=np.zeros_like(Hp); el_lab,ne=ndimage.label(ears&(b[...,3]>=HA),structure=np.ones((3,3)))
for i in range(1,ne+1):
    ys_,xs_=np.nonzero(el_lab==i)
    if len(ys_)<100: continue
    P=np.stack([xs_,ys_],1); hv=P[ConvexHull(P).vertices]; hull|=poly(hv)
side=np.zeros_like(Hp)
for jx,jy in CR.get('ear_jaw_junctions',[]):   # head side behind each ear: ellipse side point -> ear/jaw junction -> midline
    sx=cx-ax if jx<cx else cx+ax
    side|=poly([(sx,cy),(jx,jy),(cx,jy),(cx,cy)])
EARF=np.zeros_like(Hp)
for pts in CFG.get('ear_fill_polys',[]): EARF|=poly(pts)   # own fit: ear hollow + ear/head gap that only hair covered -> skin (only hair-mask px change)
EARF&=M
def smooth_closed(pts,n=24):   # Catmull-Rom through the control points (closed), own fit per view
    P=np.array(pts,float); out_=[]
    for i in range(len(P)):
        p0,p1,p2,p3=P[i-1],P[i],P[(i+1)%len(P)],P[(i+2)%len(P)]
        for t in np.linspace(0,1,n,endpoint=False):
            out_.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
    return out_
CP=np.zeros_like(Hp)
if CR.get('cranium_poly'): CP=poly(smooth_closed(CR['cranium_poly']))
for pts in CR.get('extra_polys',[]): CP|=poly(pts)
E|=CP
body=F|ears|EL|E|hull|side|EARF
C=ndimage.binary_fill_holes(body)
_sb0,_sb1=CFG.get('skin_sample_band',[150,200])   # back view: no face skin above the ears, sample the nape/neck
skin_rgb=np.median(b[F&skincls&(yy<_sb1)&(yy>_sb0)][:,:3],0).astype(int)
skin_sampled=skin_rgb.tolist()
if 'skin_detect_ref_rgb' in CFG: skin_rgb=np.array(CFG['skin_detect_ref_rgb'])   # detection reference only (the A-pose sampled median); fill = FILL below
out=b.copy()
out[M]=0
fill=M&C; out[fill,:3]=skin_rgb; out[fill,3]=255
nb=~C; edge=np.zeros_like(C)
edge[1:]|=nb[:-1]; edge[:-1]|=nb[1:]; edge[:,1:]|=nb[:,:-1]; edge[:,:-1]|=nb[:,1:]
line=fill&edge
out[line,:3]=lrgb; out[line,3]=255
eln=EL&M; out[eln,:3]=lrgb; out[eln,3]=255
# --- forehead/temple cleanup: ghost hairline (light rim) + strand ink left on the skin -> flat skin ---
# zone: head region above the ear tops, minus the eye/brow lock (holes filled = skin between brow and lid stays), mouth, hand, nose, beauty marks,
# minus the 1 px outline ring of the head region (cranium line / her outline). Cleared = non-skin components (|rgb-skin|>20) that touch the hair
# mask (<=4 px), plus their 1 px halo where |rgb-skin|>8. Components far from hair (inner brow tips, nose-bridge shading) are her art and stay.
eye_fill=ndimage.binary_fill_holes(locks['eye_brow']) if 'eye_brow' in locks else np.zeros_like(M)
ringC=C&~ndimage.binary_erosion(C,structure=np.ones((3,3)))
FTZ=C&(yy<EAR_TOP)&~eye_fill&~ringC&~KEEP
for k_ in ['mouth','hand','nose','beauty_marks']+list(CFG.get('extra_locks',{})):
    if k_ in locks: FTZ&=~locks[k_]
cdo=np.abs(out[...,:3]-skin_rgb).sum(-1)
dM=ndimage.distance_transform_edt(~M)
nsk=FTZ&(cdo>20)
lb,nl=ndimage.label(nsk,structure=np.ones((3,3)))
near=ndimage.minimum(dM,lb,range(1,nl+1)) if nl else []
NEAR=12   # was 4; strand ink freed by the v3 lock trim sits 5-12 px from the hair mask (inner brow tips / nose-bridge art are >=30 px away)
core=np.isin(lb,[i+1 for i in range(nl) if near[i]<=NEAR])
clean=FTZ&(core|(ndimage.binary_dilation(core,structure=np.ones((3,3)))&(cdo>8)))
kept_far=nsk&~core
# her forehead/temple skin carries a faint noise halo along the old hairline (|rgb-skin| ~7-20); next to the flat fill it reads as a ghost
# hairline, so the remaining skin-coloured px of the zone (|rgb-skin|<=20) are flattened too, except within 4 px of the kept art
# (inner brow tips / nose-bridge shading) and darker-than-skin px within 2 px of the eye/brow lock (brow antialias stays as drawn).
protect=ndimage.binary_dilation(kept_far,structure=np.ones((3,3)),iterations=4)|(ndimage.binary_dilation(locks.get('eye_brow',np.zeros_like(M)),structure=np.ones((3,3)),iterations=2)&(out[...,:3].sum(-1)<skin_rgb.sum()))   # only darker-than-skin px next to the lock (possible brow antialias) are protected; light rim px are hairline edge
flat_skin=FTZ&~clean&(cdo<=20)&(cdo>0)&~protect
clean|=flat_skin
out[clean,:3]=skin_rgb; out[clean,3]=255
# --- Base Hair hand-offs (A-pose): ear-strand crescents -> hair_front (body = flat skin), flyaways -> alpha 0, brow strand (above-only variant) -> flat skin ---
userlocks=locks.get('eye_brow',np.zeros_like(M))|locks.get('mouth',np.zeros_like(M))|locks['hand']
def pxset(path,pred):
    q=np.zeros_like(M)
    if os.path.exists(path):
        for p in json.load(open(path))['pixels']:
            if pred(p): q[p['y'],p['x']]=True
    return q
EJ=f'{ROOT}/hair/staged/ear_strands/{V}/for_base_body/ear_strand_px.json'
BJ=f'{ROOT}/hair/staged/brow_strand/{V}/variant_above_only/for_eyes_body/brow_strand_px.json'   # chosen variant: 24 px above the brow only (NOT the 35 px list in the parent folder)
cres_all=pxset(EJ,lambda p:'crescent' in p['group']); fly=pxset(EJ,lambda p:'flyaway' in p['group'])
brow_all=pxset(BJ,lambda p:True)   # all 24 px of the variant list; crossing (18) + below-brow (11) px stay body/lock
cres=cres_all&~userlocks; brow=brow_all&~userlocks
out[cres|brow,:3]=skin_rgb; out[cres|brow,3]=255
out[fly&~userlocks]=0
handoff_px=cres|brow|(fly&~userlocks)
# Hair's hand-off px are hair, not face: drop them from Body's own face-oval / beauty-mark boxes (the moles are elsewhere in the box; checked by eye)
face&=~handoff_px; beauty&=~handoff_px; locks['face_oval_nonhair']=face; locks['beauty_marks']=beauty
out[out[...,3]==0]=0
if CFG.get('keep_alpha0_rgb'): _z=(out[...,3]==0)&(b[...,3]==0); out[_z]=b_raw[_z]   # left/right/back: transparent px she left transparent keep their exact bytes (0 px change in locks, byte for byte)
# fill colour: her real flat skin (186,129,86) (36,620 px in views/apose/base.png; (186,129,85) never occurs there). The detection above keeps
# using skin_rgb as the reference; every px this script wrote with skin_rgb gets FILL. Her own px that already have that colour stay as drawn.
FILL=np.array(CFG.get('fill_rgb',[186,129,86]))
wrote=(out!=b).any(-1)&(out[...,3]==255)&(out[...,:3]==skin_rgb).all(-1)
out[wrote,:3]=FILL; fill_recoloured=int(wrote.sum())
Image.fromarray(out.astype(np.uint8),'RGBA').save(f'{OUT}/hairless_{V}.png')
def save(mask,name): Image.fromarray((mask*255).astype(np.uint8),'L').save(f'{OUT}/{name}')
save(M,'hair_mask_used.png'); save(clean,'forehead_clean_mask.png'); save(handoff_px,'hair_handoff_px_mask.png'); save(FTZ,'forehead_clean_zone.png'); save(Hp,'hair_mask_part_union_visible.png'); save(resid|S|fringe,'hair_mask_residual_specks_fringe.png')
facelock=locks.get('eye_brow',np.zeros_like(M))|locks.get('mouth',np.zeros_like(M))|nose|beauty|face
save(INK_keep,'kept_ink_mask.png') if CFG.get('other_views_ink') else None; save(facelock,'face_lock_mask.png'); save(C,'head_body_region.png')
changed=(out!=b).any(-1)
rep={'view':V,'hair_mask_px':int(M.sum()),'components':{'visible_hair_part_px':int(Hp.sum()),'specks_px':int((S&~Hp).sum()),'residual_hair_px':int(resid.sum()),'hairline_fringe_px':int(fringe.sum()),'erase_mask_extra':int((erase&~Hp).sum())},
 'sweep_mask':bool(sweep is not None),
 'changed_px_total':int(changed.sum()),'changed_outside_hair_mask':int((changed&~M).sum()),'changed_outside_hair_mask_and_forehead_clean':int((changed&~M&~clean&~handoff_px).sum()),
 'hair_handoff':{'crescent_px':int(cres_all.sum()),'crescent_to_skin':int(cres.sum()),'crescent_kept_in_locks':int((cres_all&userlocks).sum()),'flyaway_px':int(fly.sum()),'flyaway_alpha0_after':int((fly&(out[...,3]==0)).sum()),'flyaway_changed_vs_base':int((fly&changed).sum()),'brow_above_px':int(brow_all.sum()),'brow_to_skin':int(brow.sum()),'brow_in_locks':int((brow_all&userlocks).sum())},
 'forehead_clean':{'cleared_to_flat_skin_px':int(clean.sum()),'of_which_outside_hair_mask':int((clean&~M).sum()),'components':int(len([1 for i in range(nl) if near[i]<=NEAR])),'kept_far_from_hair_px':int(kept_far.sum()),'flattened_skin_noise_px':int(flat_skin.sum()),'ear_top_row':EAR_TOP,'eye_lock_px':int(locks['eye_brow'].sum()) if 'eye_brow' in locks else None},
 'lock_changed':{k_:int((changed&L).sum()) for k_,L in locks.items()},'face_lock_total_changed':int((changed&facelock).sum()),
 'filled_skin_px':int((fill&~line&~eln).sum()),'cranium_line_px':int(line.sum()),'ear_line_fill_dropped_floating':EL_dropped,'ear_fill_poly_px':int(EARF.sum()),'ear_line_px':int(eln.sum()),'cleared_to_alpha0_px':int((M&~C).sum()),
 'kept_ink_other_views':{'listed_px_in_source':int(INK.sum()),'cut_into_staged_hair_part_px':int(INK_cut.sum()),'kept_as_drawn_px':int(INK_keep.sum()),'kept_components':[dict(kind=k,px=int((q&INK_keep).sum()),x=[int(np.nonzero(q)[1].min()),int(np.nonzero(q)[1].max())],y=[int(np.nonzero(q)[0].min()),int(np.nonzero(q)[0].max())]) for k,q in ink_list if (q&INK_keep).any()]},
 'skin_rgb':FILL.tolist(),'skin_detect_ref_rgb':skin_rgb.tolist(),'skin_rgb_sampled':skin_sampled,'fill_px_written_in_skin_rgb':fill_recoloured,'native_px_in_detect_ref_colour_kept':int(((b[...,:3]==skin_rgb).all(-1)&(b[...,3]>0)&~wrote&((out[...,:3]==skin_rgb).all(-1))).sum()),'source':SRC or f'views/{V}/base.png','keep_boxes':CFG.get('keep_boxes',[]),'line_rgb':lrgb.tolist()}
json.dump(rep,open(f'{OUT}/hairless_report.json','w'),indent=1); print(json.dumps(rep,indent=1))
