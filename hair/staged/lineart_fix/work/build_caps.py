# Proposal (STAGED ONLY): joint overlap caps / static underfills for the joints that fail the lineart check.
#   python3 build_caps.py <src_hairroot> <lineart_json> <dst_hairroot> [radius]
# For each failing joint child<-parent: the child's alpha-255 px within `radius` px of the child's pivot that the parent does not
# already have are copied (exact RGBA, they are base.png copies) into the parent PNG.
#  - parent swaying and drawn ABOVE the child -> a hidden joint cap (validate_hair rule 4: both opaque, parent layer higher)
#  - parent static (hair_front / hair_back)   -> a static underfill drawn under the strand root (hidden at rest by the strand)
import sys, os, json, shutil, numpy as np
from PIL import Image
src,lj,dst=sys.argv[1:4]; r=float(sys.argv[4]) if len(sys.argv)>4 else 4
L=json.load(open(lj)); log={}
for v in L:
    s=f'{src}/{v}/hair'; d=f'{dst}/{v}/hair'; os.makedirs(d,exist_ok=True)
    for f in os.listdir(s):
        if f.endswith('.png') or f=='rig.json': shutil.copy2(os.path.realpath(f'{s}/{f}'),f'{d}/{f}')
    rig=json.load(open(f'{d}/rig.json'))['parts']; by={e['id']:e for e in rig}
    for k,j in L[v]['joints'].items():
        if j['PASS']: continue
        c,q=k.split('<-'); C=by[c]; Q=by[q]
        ca=np.array(Image.open(f"{d}/{C['file']}").convert('RGBA')); qa=np.array(Image.open(f"{d}/{Q['file']}").convert('RGBA'))
        H,W=ca.shape[:2]; yy,xx=np.mgrid[0:H,0:W]
        sel=(ca[...,3]==255)&(qa[...,3]==0)&(np.hypot(xx+.5-C['pivotX'],yy+.5-C['pivotY'])<=r)
        kind='cap' if Q['swayWeight']>0 else 'underfill'
        if kind=='cap' and not Q['layer']>C['layer']: log.setdefault(v,{})[k]='skipped: parent not above child'; continue
        qa[sel]=ca[sel]; Image.fromarray(qa,'RGBA').save(f"{d}/{Q['file']}")
        ys,xs=np.nonzero(sel); log.setdefault(v,{})[k]=dict(kind=kind,into=Q['file'],px=int(sel.sum()),xy=[[int(x),int(y)] for x,y in zip(xs,ys)])
json.dump(log,open(f'{dst}/caps_log.json','w'),indent=1); print(json.dumps({v:{k:(x if isinstance(x,str) else (x['kind'],x['px'])) for k,x in d.items()} for v,d in log.items()}))
