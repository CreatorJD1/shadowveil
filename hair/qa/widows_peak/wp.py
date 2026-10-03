# Job 6: widow's-peak light outline = design px (user). Locate, build allow-list masks, verify no staged hair fix touched them.
import glob,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
R='/workspace/shadowveil'; OUT=R+'/hair/qa/widows_peak'; res={}
SEED={'apose':(660,705,150,180),'tpose':(662,702,150,175)}
for v in ['apose','tpose','left','right','back']:
    b=np.array(Image.open(f'{R}/views/{v}/base.png').convert('RGBA')).astype(int); a=b[...,3]; L=b[...,:3].mean(-1)
    dark=(a>0)&(b[...,:3].max(-1)<90); m=np.zeros(a.shape,bool)
    if v in SEED:
        x0,x1,y0,y1=SEED[v]; box=np.zeros(a.shape,bool); box[y0:y1+1,x0:x1+1]=True
        m=box&(a>0)&(L>=160)&nd.binary_dilation(dark,iterations=2)
    Image.fromarray((m*255).astype(np.uint8)).save(f'{OUT}/{v}_widows_peak_mask.png')
    region=nd.binary_dilation(m,iterations=3) if m.any() else m
    chk={}
    for f in sorted(glob.glob(f'{R}/hair/staged/**/*.png',recursive=True)):
        rel=f[len(R)+1:]
        if f'/{v}/' not in rel or '/hair/' not in rel[len('hair/staged'):] or 'for_' in rel or '/work' in rel: continue
        name=f.rsplit('/',1)[1]; live=f'{R}/views/{v}/hair/{name}'
        try: s=np.array(Image.open(f).convert('RGBA')).astype(int); l=np.array(Image.open(live).convert('RGBA')).astype(int)
        except Exception: continue
        if s.shape!=l.shape: continue
        chk[f[len(R)+1:]]=dict(diff_in_region=int(((s!=l).any(-1)&region).sum()),alpha_on_mask=int((s[...,3][m]>0).sum()),live_alpha_on_mask=int((l[...,3][m]>0).sum()))
    ys,xs=np.nonzero(m)
    res[v]=dict(px=int(m.sum()),bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if m.any() else None,
        rgba_range=dict(min=b[m].min(0).tolist(),max=b[m].max(0).tolist()) if m.any() else None,staged_files_checked=len(chk),
        staged_files_with_diff=[k for k,x in chk.items() if x['diff_in_region']],files=chk)
    print(v,res[v]['px'],res[v]['bbox'],'checked',len(chk),'with diff',res[v]['staged_files_with_diff'])
json.dump(res,open(f'{OUT}/widows_peak.json','w'),indent=1)
