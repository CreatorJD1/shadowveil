# Builds the STAGED speck fix (writes only under hair/staged/speck_fix/). Reads live files read-only.
# For every speck px in the proposal: strand px := base.png px (exact RGBA copy); erase mask px := 255.
import json, os, hashlib, numpy as np
from PIL import Image
R='/workspace/shadowveil'; ST=R+'/hair/staged/speck_fix'; P=R+'/hair/qa/wisp_fix/erase_mask_proposal'
prop=json.load(open(P+'/proposal.json')); manifest={'files':[],'pixels':{}}
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
for v in ['apose','tpose','left','right','back']:
    base=np.array(Image.open(f'{R}/views/{v}/base.png').convert('RGBA'))
    rig=json.load(open(f'{R}/views/{v}/hair/rig.json'))['parts']; fby={e['id']:e['file'] for e in rig}
    allpx=np.zeros(base.shape[:2],bool); manifest['pixels'][v]={}
    for sid,px in prop[v]['pixels_xy'].items():
        rel=f'views/{v}/hair/{fby[sid]}'; live=f'{R}/{rel}'
        im=Image.open(live); assert im.mode=='RGBA'; a=np.array(im)
        rows=[]
        for x,y in px:
            assert a[y,x,3]==0, (v,sid,x,y,'strand px not empty')
            assert not allpx[y,x]
            a[y,x]=base[y,x]; allpx[y,x]=True; rows.append([x,y]+[int(c) for c in base[y,x]])
        out=f'{ST}/{rel}'; os.makedirs(os.path.dirname(out),exist_ok=True); Image.fromarray(a,'RGBA').save(out)
        manifest['files'].append(dict(staged=rel,live_sha256_at_staging=sha(live),staged_sha256=sha(out),px_added=len(px)))
        manifest['pixels'][v][sid]=rows
    rel=f'hair/{v}_hair_erase_mask.png'; live=f'{R}/{rel}'
    m=np.array(Image.open(live)); assert m.ndim==2
    assert not (m[allpx]>127).any()
    add=np.array(Image.open(f'{P}/{v}_hair_erase_mask_ADD.png').convert('L'))>127
    assert (add==allpx).all()
    m2=m.copy(); m2[allpx]=255
    out=f'{ST}/{rel}'; os.makedirs(os.path.dirname(out),exist_ok=True); Image.fromarray(m2,'L').save(out)
    assert (np.array(Image.open(f'{P}/{v}_hair_erase_mask_PROPOSED.png').convert('L'))>127).__eq__(m2>127).all()
    Image.fromarray((allpx*255).astype(np.uint8),'L').save(f'{ST}/for_base_body/{v}_speck_px_ADD.png') if os.path.isdir(f'{ST}/for_base_body') else None
    manifest['files'].append(dict(staged=rel,live_sha256_at_staging=sha(live),staged_sha256=sha(out),px_added=int(allpx.sum())))
    print(v,int(allpx.sum()))
json.dump(manifest,open(f'{ST}/manifest.json','w'),indent=1)
