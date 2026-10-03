# Recolour opaque (186,129,85) -> (186,129,86) in every staged png under hairless_division_staged/ (2026-10-02, per team: 85 is not her colour;
# her flat skin is (186,129,86)). Full-canvas files of tpose/left/right/back keep px that are (186,129,85) in her live art at the same
# position (views/<v>/base.png or base_body.png): those are drawn by her, not our fill. Writes recolour_skin85_report.json.
import os,json,numpy as np
from PIL import Image
R='/workspace/shadowveil'; WD=R+'/body_tools/work/hairless_division_staged'
OLD=np.array([186,129,85]); NEW=np.array([186,129,86])
nat={}
for v in ['tpose','left','right','back']:
    m=None
    for n in ['base','base_body','base_body_skin']:
        a=np.array(Image.open(f'{R}/views/{v}/{n}.png').convert('RGBA')).astype(int)
        k=(a[...,:3]==OLD).all(-1)&(a[...,3]>0); m=k if m is None else m|k
    nat[v]=m
rep={}
for dp,_,fs in os.walk(WD):
    for f in sorted(fs):
        if not f.endswith('.png'): continue
        p=os.path.join(dp,f); rel=os.path.relpath(p,WD); im=Image.open(p)
        if im.mode not in ('RGB','RGBA'): continue
        a=np.array(im).astype(int); op=(a[...,3]>0) if im.mode=='RGBA' else np.ones(a.shape[:2],bool)
        m=(a[...,:3]==OLD).all(-1)&op
        if not m.any(): continue
        v=rel.split('/')[0]; keep=np.zeros_like(m)
        if v in nat and a.shape[:2]==nat[v].shape: keep=m&nat[v]
        ch=m&~keep
        if ch.any():
            a[ch,:3]=NEW; Image.fromarray(a.astype(np.uint8),im.mode).save(p)
        rep[rel]={'recoloured':int(ch.sum()),'kept_native_her_art':int(keep.sum())}
json.dump(rep,open(f'{WD}/recolour_skin85_report.json','w'),indent=1)
print(json.dumps({k:v for k,v in rep.items()}))
