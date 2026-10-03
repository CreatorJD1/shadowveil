# STAGED copies of views/<view>/base_body.png + base_body_skin.png (live never written).
#   apose: Hair ear-strand hand-off (flyaway px -> alpha 0; eye-corner crescent px -> flat skin (186,129,86,255) (her real flat skin; was 85 before 2026-10-02 23:20 PT) unless inside the eye/brow lock)
#   all five views: Hair speck_fix px (hair/staged/speck_fix/for_base_body/<view>_speck_px_ADD.png, 413 px total) -> alpha 0
#     (PIXELS.md: "clear these pixels to alpha 0 in base_body.png and base_body_skin.png ... no skin fill under them")
#   apose, tpose, left, right, back (views with hairless pieces): base_body_skin.png cut to alpha 0 (rgba 0) inside <view>/hand_mask.png, the same cut as the
#     body pieces (hands are drawn under the forearms; otherwise skin shows at rest). base_body.png is not hand-cut.
#     Hand px that a piece fills (left/right: flat under-hand skin on the thigh, the thigh continues under the hand) are NOT cut (apose/tpose/back: none).
#   right: the round-2 staged base_body_skin.png (body_tools/work/round2_staged/) also gets the specks -> round2_staged/with_specks/
# Usage: python3 make_live_patch.py [view ...]   (default: all five)
import json,os,sys,numpy as np
from PIL import Image as I
R='/workspace/shadowveil'; WD=R+'/body_tools/work/hairless_division_staged'
VIEWS=sys.argv[1:] or ['apose','tpose','left','right','back']
def mask(p):
    if not os.path.exists(p): return None
    a=np.array(I.open(p)); return (a[...,-1] if a.ndim==3 else a)>127
def locks(v):
    L={}
    for k,p in [('eye_brow',f'{R}/eyes/handoff_hairless/{v}_eye_brow_lock.png'),('mouth',f'{R}/mouth/handoff_hairless/{v}_mouth_lock.png'),('hand',f'{R}/hands/{v}_hand_erase_mask.png')]:
        m=mask(p)
        if m is not None: L[k]=m
    return L
def patch(src,dst,v,lk,rep_key,rep):
    a=np.array(I.open(src).convert('RGBA')); a0=a.copy(); r={}
    if v=='apose':
        j=json.load(open(R+'/hair/staged/ear_strands/apose/for_base_body/ear_strand_px.json'))
        eye=lk.get('eye_brow'); c=f=kl=0
        for p in j['pixels']:
            y,x=p['y'],p['x']
            if 'flyaway' in p['group']: a[y,x]=0; f+=1
            elif eye is not None and eye[y,x]: kl+=1
            else: a[y,x]=[186,129,86,255]; c+=1
        r.update(ear_flyaway_alpha0=f,ear_crescent_to_skin=c,ear_crescent_kept_in_eye_lock=kl)
    sm=mask(f'{R}/hair/staged/speck_fix/for_base_body/{v}_speck_px_ADD.png')
    r['speck_px']=int(sm.sum()); r['speck_px_alpha_before']={'255':int((a0[sm][:,3]==255).sum()),'lt255':int((a0[sm][:,3]<255).sum())}
    a[sm]=0
    hm=mask(f'{WD}/{v}/hand_mask.png')   # every view with hairless pieces (apose, tpose, left, right, back): hand_mask.png written by divide.py
    if hm is not None and os.path.basename(src)=='base_body_skin.png':   # also the right round-2 skin copy
        hm_all=hm.copy(); U=np.zeros_like(hm)   # same cut as the pieces: hand px that a piece fills (profile under-hand thigh fill) stay skin
        for pf in os.listdir(f'{WD}/{v}/pieces'):
            if pf.endswith('.png'): U|=np.array(I.open(f'{WD}/{v}/pieces/{pf}'))[...,3]>0
        hm=hm&~U; r['hand_mask_px']=int(hm_all.sum()); r['hand_px_kept_under_piece_fill']=int((hm_all&U).sum())
        r['hand_cut_px']=int(hm.sum()); r['hand_cut_opaque_before']=int((a[hm][:,3]>0).sum()); r['hand_cut_rgba_changed']=int((a[hm]!=0).any(-1).sum())
        a[hm]=0; r['hand_mask']=os.path.relpath(f'{WD}/{v}/hand_mask.png',R)
    ch=(a!=a0).any(-1)
    r['px_changed_vs_source']=int(ch.sum()); r['speck_alpha0_after']=int((a[sm][:,3]==0).sum())
    r['changed_inside_locks']={k:int((ch&m).sum()) for k,m in lk.items()}
    os.makedirs(os.path.dirname(dst),exist_ok=True); I.fromarray(a,'RGBA').save(dst)
    r['src']=os.path.relpath(src,R); r['dst']=os.path.relpath(dst,R); rep[rep_key]=r
for v in VIEWS:
    LP=f'{WD}/{v}/live_patch_staged'; lk=locks(v); rep={'view':v,'note':'STAGED copies, live untouched','locks_checked':sorted(lk)}
    for nm in ['base_body.png','base_body_skin.png']:
        patch(f'{R}/views/{v}/{nm}',f'{LP}/{nm}',v,lk,nm,rep)
    if v=='right' and os.path.exists(f'{R}/body_tools/work/round2_staged/base_body_skin.png'):
        patch(f'{R}/body_tools/work/round2_staged/base_body_skin.png',f'{R}/body_tools/work/round2_staged/with_specks/base_body_skin.png',v,lk,'round2_base_body_skin.png',rep)
        a=np.array(I.open(f'{R}/body_tools/work/round2_staged/with_specks/base_body_skin.png')); b=np.array(I.open(f'{LP}/base_body_skin.png'))
        rep['round2_with_specks_equals_live_patch_skin']=bool((a==b).all())
    json.dump(rep,open(f'{LP}/live_patch_report.json','w'),indent=1); print(json.dumps(rep))
