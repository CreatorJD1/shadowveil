import json,numpy as np,os
from PIL import Image
out={}
for v in ['apose','tpose','left','right','back']:
    d={}
    for owner in ['eyes','mouth']:
        p=f'views/{v}/{owner}/rig.json'
        if not os.path.exists(p): continue
        j=json.load(open(p)); ps=j if isinstance(j,list) else j.get('parts',[])
        extra={k:j[k] for k in j if k not in('parts',)} if isinstance(j,dict) else {}
        groups={}
        for q in ps:
            f=q.get('file')
            if not f or f.endswith('_chroma.png'): continue
            a=np.array(Image.open(f'views/{v}/{owner}/{f}').convert('RGBA'))[...,3]
            ys,xs=np.nonzero(a>0)
            if not len(xs): continue
            key=('EyeL' if q['id'].startswith('EyeL') else 'EyeR' if q['id'].startswith('EyeR') else 'mouth')
            bb=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
            g=groups.setdefault(key,{'all':bb[:],'open':None})
            g['all']=[min(g['all'][0],bb[0]),min(g['all'][1],bb[1]),max(g['all'][2],bb[2]),max(g['all'][3],bb[3])]
            if key=='mouth' and q['id'].endswith('rest'): g['open']=bb
            if key!='mouth' and any(q['id'].endswith(s) for s in ('_white','_iris','_lash','_lid_0')):
                o=g['open'] or bb; g['open']=[min(o[0],bb[0]),min(o[1],bb[1]),max(o[2],bb[2]),max(o[3],bb[3])]
        d.update(groups)
        d[owner+'_extra']={k:(v2 if len(json.dumps(v2))<300 else '...') for k,v2 in extra.items()}
    out[v]=d
json.dump(out,open('hair/qa/idle_battle/work/boxes.json','w'),indent=1)
print(json.dumps(out,indent=0)[:4000])
