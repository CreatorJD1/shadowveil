# Analysis for render.py output: background/chroma px inside her rest silhouette (base.png alpha>=250) at each sway pose,
# live default rig vs ?hairless=1 final set. NEW = see-through in hairless but not in live (pixel set difference).
import json,re,os,numpy as np
from PIL import Image
from scipy import ndimage as nd
R='/workspace/shadowveil'; D=R+'/hair/qa/sway_over_hairless_final'; W=D+'/work'
L=lambda f:np.array(Image.open(f).convert('RGBA')).astype(int)
t=open(R+'/rig/index.html').read(); HMAP=json.loads(re.search(r'const HAIRLESS_HAIR=(\{.*?\});',t).group(1))
def hpath(v,f,final): u=f'../views/{v}/hair/{f}'; return R+'/'+(HMAP.get(u,u) if final else u)[3:]
def holes(a):
    tt=a<250; lab,n=nd.label(tt); b=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]])); return np.isin(lab,[i for i in range(1,n+1) if i not in b])
POSES=['sx+1','sx+1sy+1','sx+1sy-1','sx-1','sx-1sy+1','sx-1sy-1','sy+1','sy-1','whip+1','whip+1sy+1','whip+1sy-1','whip-1','whip-1sy+1','whip-1sy-1']
out={}; md=['# Sway-over-hairless see-through, FINAL set (rerun)','']
for v in ['apose','tpose','left','right','back']:
    if not os.path.exists(f'{W}/{v}_meta.json'): continue
    meta=json.load(open(f'{W}/{v}_meta.json')); base=L(f'{R}/views/{v}/base.png'); inside=base[...,3]>=250
    rig=json.load(open(hpath(v,'rig.json',True)))['parts']
    rest_hair={p['id']:L(hpath(v,p['file'],True))[...,3] for p in rig if p.get('file')}
    bodyL={b:L(f'{R}/views/{v}/{b}.png')[...,3] for b in ('base_body','base_body_skin')}
    bodyF={b:L(f'{R}/body_tools/work/hairless_division_staged/{v}/live_patch_staged/{b}.png')[...,3] for b in ('base_body','base_body_skin')}
    o=out[v]={'rest':{t:{k:meta[t][k] for k in ('restPixels_vs_base','restCheck','missing')} for t in meta}}
    for tag in ('live','hairless'):
        A=L(f'{W}/{v}_{tag}_rest.png'); o['rest'][tag]['frame_vs_base_px']=int((np.abs(A-base).max(-1)>0)[(A[...,3]>0)|(base[...,3]>0)].sum())
    worst=None
    for p in POSES:
        S={}; F={}
        for tag in ('live','hairless'):
            A=L(f'{W}/{v}_{tag}_{p}.png'); F[tag]=A
            blue=(A[...,3]>=128)&(A[...,2]>A[...,0]+30)&(A[...,2]>120)&(A[...,2]>A[...,1]+30)
            S[tag]=dict(see=inside&(A[...,3]<250),enc=holes(A[...,3])&inside,blue=blue&inside&~(base[...,2]>base[...,0]+30))
        new=S['hairless']['see']&~S['live']['see']; fixed=S['live']['see']&~S['hairless']['see']
        newb=S['hairless']['blue']&~S['live']['blue']
        r=dict(live_px=int(S['live']['see'].sum()),hairless_px=int(S['hairless']['see'].sum()),new_px=int(new.sum()),fixed_px=int(fixed.sum()),
               live_enclosed=int(S['live']['enc'].sum()),hairless_enclosed=int(S['hairless']['enc'].sum()),
               new_enclosed=int((S['hairless']['enc']&~S['live']['enc']).sum()),new_blue_px=int(newb.sum()),
               live_head_y430=int((S['live']['see'][:430]).sum()),hairless_head_y430=int((S['hairless']['see'][:430]).sum()))
        lab,n=nd.label(new|newb,np.ones((3,3))); comps=[]
        for i,sl in enumerate(nd.find_objects(lab),1):
            m=lab==i; ys,xs=np.nonzero(m)
            parts=sorted({k for k,a in rest_hair.items() if (a[m]>0).any()})
            bod={b:dict(live_opaque=int((bodyL[b][m]>=250).sum()),final_opaque=int((bodyF[b][m]>=250).sum())) for b in bodyL}
            comps.append(dict(px=int(m.sum()),bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],hair_parts_covering_at_rest=parts,body=bod))
        r['new_components']=comps; o[p]=r
        if worst is None or r['new_px']+r['new_blue_px']>o[worst]['new_px']+o[worst]['new_blue_px'] or (r['new_px']==0 and o[worst]['new_px']==0 and r['hairless_px']>o[worst]['hairless_px']): worst=p
        if p==worst: Fw,Sw,neww,fixw=F,S,new|newb,fixed
    # overlay of the worst pose: hairless frame greyed, yellow = see-through in both, red = NEW, cyan = live-only
    A=Fw['hairless']; g=(A[...,:3].mean(-1)*0.5+127).astype(np.uint8); img=np.stack([g,g,g],-1)
    both=Sw['live']['see']&Sw['hairless']['see']; img[both]=(255,200,0); img[fixw]=(0,200,255); img[neww]=(255,0,0)
    Image.fromarray(img).save(f'{D}/overlay_{v}.png'); o['worst_pose']=worst
    agg=dict(max_live=max(o[p]['live_px'] for p in POSES),max_hairless=max(o[p]['hairless_px'] for p in POSES),max_new=max(o[p]['new_px'] for p in POSES),
             max_new_enclosed=max(o[p]['new_enclosed'] for p in POSES),max_new_blue=max(o[p]['new_blue_px'] for p in POSES))
    o['summary']=agg; print(v,o['rest']['live']['restPixels_vs_base'],o['rest']['hairless']['restPixels_vs_base'],agg,'worst',worst,flush=True)
    for p in POSES: print('  ',p,{k:o[p][k] for k in o[p] if k!='new_components'},o[p]['new_components'][:4])
    a=json.load(open(f'{W}/{v}_auto.json')); o['presetA_auto']={t:dict(frames=len(a[t]),seconds=a[t][-1]['t'] if a[t] else 0,max_abs_drive=max(f['maxDrive'] for f in a[t])) for t in a}
json.dump(out,open(f'{D}/results.json','w'),indent=1)
