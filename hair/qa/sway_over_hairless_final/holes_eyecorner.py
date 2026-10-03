# (1) hairfront_holes: hole px alpha in ?hairless=1 (with fix, as index.html maps it) vs hlnofix (hair_front swapped back to the pre-fix
#     file by request interception); (2) A-pose eye-corner region x612-619/x746-752 y214-238 (Body's flat-skin px under hair_front).
import json,numpy as np
from PIL import Image
L=lambda f:np.array(Image.open(f).convert('RGBA')).astype(int)
R='/workspace/shadowveil'; W='work'
P=['rest','sx+1','sx+1sy+1','sx+1sy-1','sx-1','sx-1sy+1','sx-1sy-1','sy+1','sy-1','whip+1','whip+1sy+1','whip+1sy-1','whip-1','whip-1sy+1','whip-1sy-1']
px={'apose':(604,129),'right':(780,169)}; res={}
for v,(x,y) in px.items():
    base=L(f'{R}/views/{v}/base.png'); ins=base[...,3]>=250; res[v]={}
    for p in P:
        F=L(f'{W}/{v}_hairless_{p}.png'); H=L(f'{W}/{v}_hlnofix_{p}.png'); Lv=L(f'{W}/{v}_live_{p}.png')
        diff=(F!=H).any(-1); sF=ins&(F[...,3]<250); sH=ins&(H[...,3]<250); sL=ins&(Lv[...,3]<250)
        res[v][p]=dict(hole_alpha_nofix=int(H[y,x,3]),hole_alpha_fix=int(F[y,x,3]),px_changed=int(diff.sum()),changed_outside_hole=int(diff.sum()-diff[y,x]),
            see_live=int(sL.sum()),see_nofix=int(sH.sum()),see_fix=int(sF.sum()),new_vs_live_nofix=int((sH&~sL).sum()),new_vs_live_fix=int((sF&~sL).sum()),newly_see_through_from_fix=int((sF&~sH).sum()))
    print(v,'hole open (alpha<255) poses nofix',sum(r['hole_alpha_nofix']<255 for r in res[v].values()),'fix',sum(r['hole_alpha_fix']<255 for r in res[v].values()),
          'max changed outside hole',max(r['changed_outside_hole'] for r in res[v].values()),'newly see-through',max(r['newly_see_through_from_fix'] for r in res[v].values()))
json.dump(res,open(f'{R}/hair/staged/hairfront_holes/verify_sway.json','w'),indent=1)
# eye-corner
F='body_tools/work/hairless_division_staged/apose/live_patch_staged/'
base=L(f'{R}/views/apose/base.png'); bl=L(f'{R}/views/apose/base_body.png'); bf=L(f'{R}/{F}base_body.png'); sf=L(f'{R}/{F}base_body_skin.png')
reg=np.zeros(base.shape[:2],bool); reg[214:239,612:620]=True; reg[214:239,746:753]=True
ch=((bl!=bf).any(-1))&reg
hf=L(f'{R}/hair/staged/hairfront_holes/apose/hair/hair_front.png')
cols=set(map(tuple,base[base[...,3]==255][:,:3].tolist()))
ec=dict(region_px=int(reg.sum()),body_changed=int(ch.sum()),changed_L=int(ch[:,:700].sum()),changed_R=int(ch[:,700:].sum()),
  hair_front_alpha255_on_changed=int((hf[...,3]==255)[ch].sum()),
  body_final_alpha255=int((bf[...,3]==255)[ch].sum()),body_partial=int(((bf[...,3]>0)&(bf[...,3]<255))[ch].sum()),
  skin_eq_body=int((sf==bf).all(-1)[ch].sum()),colours=sorted({tuple(int(c) for c in t) for t in bf[ch][:,:3].tolist()}),
  colours_in_base_png=[c in cols for c in sorted({tuple(t) for t in bf[ch][:,:3].tolist()})],
  chroma=int(((bf[...,2]>bf[...,0]+30)&(bf[...,2]>120))[ch].sum()))
nb=np.zeros_like(ch)
for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)): nb|=(bf[...,:3]==np.roll(bf[...,:3],(dy,dx),(0,1))).all(-1)
ec['isolated_specks']=int((ch&~nb).sum())
poses={}
for p in P:
    Hh=L(f'{W}/apose_hairless_{p}.png'); Lv=L(f'{W}/apose_live_{p}.png')
    poses[p]=dict(hl_eq_live=int((Hh==Lv).all(-1)[ch].sum()),skin_visible=int(((Hh[...,:3]==bf[...,:3]).all(-1)&(Hh[...,:3]!=base[...,:3]).any(-1))[ch].sum()),alpha_lt255=int((Hh[...,3]<255)[ch].sum()))
ec['poses']=poses; print('eyecorner',{k:v for k,v in ec.items() if k!='poses'}); print('  poses min hl==live',min(q['hl_eq_live'] for q in poses.values()),'max skin visible',max(q['skin_visible'] for q in poses.values()),'max alpha<255',max(q['alpha_lt255'] for q in poses.values()))
json.dump(ec,open('eyecorner_apose.json','w'),indent=1)
