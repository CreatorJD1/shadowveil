# Hole / tear / chroma counts per render (render-only analysis).
import json, sys, numpy as np, os
from PIL import Image
from scipy import ndimage as nd
D=sys.argv[1]; log=json.load(open(f'{D}/render_log.json'))
def stats(a):
    al=a[...,3].astype(int); op=al>=128
    lab,n=nd.label(~op); border=np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]]))
    holes=(~op)&~np.isin(lab,border)
    sil=nd.binary_fill_holes(op); inner=nd.binary_erosion(sil,iterations=4)
    tear=inner&(al<240)&~holes
    rgb=a[...,:3].astype(int)
    chroma=(al>0)&(rgb[...,2]-np.maximum(rgb[...,0],rgb[...,1])>80)
    keyblue=(al>0)&(rgb[...,2]>200)&(rgb[...,0]<60)&(rgb[...,1]<60)
    return dict(holes=holes,tear=tear,chroma=chroma,keyblue=keyblue,op=op)
def comps(mask,nodes,minpx=1):
    lab,n=nd.label(mask); out=[]
    for i,sl in enumerate(nd.find_objects(lab),1):
        m=lab[sl]==i; c=int(m.sum())
        if c<minpx: continue
        ys,xs=np.nonzero(m); cy,cx=ys.mean()+sl[0].start,xs.mean()+sl[1].start
        near=min(nodes,key=lambda n:(n['pivot'][0]-cx)**2+(n['pivot'][1]-cy)**2)['key'] if nodes else None
        out.append(dict(px=c,bbox=[int(sl[1].start),int(sl[0].start),int(sl[1].stop-1),int(sl[0].stop-1)],nearJoint=near))
    return sorted(out,key=lambda o:-o['px'])
res={}; base={}
for r in log['results']:
    a=np.array(Image.open(f"{D}/{r['name']}.png").convert('RGBA')); s=stats(a)
    if r['name'].startswith('rest_'): base[r['view']]=s
    res[r['name']]=(r,s,a)
out={}
for name,(r,s,a) in res.items():
    b=base.get(r['view']); o={'view':r['view'],'stress':r['stress']}
    for k in ('holes','tear','chroma','keyblue'): o[k+'_px']=int(s[k].sum())
    if b is not None and not name.startswith('rest_'):
        nh=s['holes']&~b['holes']; nt=s['tear']&~b['tear']
        o['new_holes_px']=int(nh.sum()); o['new_tear_px']=int(nt.sum())
        o['new_hole_components']=comps(nh,r['nodes'],3)[:8]; o['new_tear_components']=comps(nt,r['nodes'],3)[:8]
        o['silhouette_px']=int(s['op'].sum()); o['rest_silhouette_px']=int(b['op'].sum())
    o['chroma_components']=comps(s['chroma'],r['nodes'],1)[:5]
    out[name]=o
    # overlay: holes red, tears yellow, chroma cyan
    ov=a.copy(); ov[...,3]=255; bg=np.zeros_like(ov); bg[...]= (40,40,40,255)
    al=a[...,3:4]/255.; comp=(a[...,:3]*al+bg[...,:3]*(1-al)).astype('uint8'); comp=np.dstack([comp,np.full(al.shape[:2],255,'uint8')])
    for m,c in ((s['holes'],(255,0,0)),(s['tear'],(255,255,0)),(s['chroma'],(0,255,255))):
        mm=nd.binary_dilation(m,iterations=2); comp[mm,:3]=c
    Image.fromarray(comp).save(f'{D}/{name}_qa.png')
json.dump(out,open(f'{D}/qa.json','w'),indent=1)
for k,o in out.items(): print(k,{x:o.get(x) for x in ('holes_px','new_holes_px','tear_px','new_tear_px','chroma_px','keyblue_px')}, [ (c['px'],c['nearJoint']) for c in o.get('new_hole_components',[])[:4]])
