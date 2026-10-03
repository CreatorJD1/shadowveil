# Hair-over-eyes/mouth check at LINEAR display quality (rig/index.html via r18.py), preset-A sway range.
#   python3 face_sway_check.py <view> <out.json> <baseline_overlay_dirs(comma, '' = live)> <staged_overlay_dirs(comma)> [part,part,...]
# Overlay dir = a folder holding views/<view>/hair/<file>.png replacements (later dirs win). Only the listed parts (default: all) are drawn.
# Poses: manual x in 41 steps [-1,1] (same x down the chain) and the auto-chain extremes, each with HairSwayY in {-1,0,+1}.
# Face = alpha>0 of views/<v>/eyes/*.png and views/<v>/mouth/*.png (no chroma/preview/sheet files). Read-only.
import sys,os,json,glob,numpy as np
from PIL import Image
R='/workspace/shadowveil'
sys.path.insert(0,R+'/hair/handoff_hairless/work'); sys.path.insert(0,R+'/hair/staged/lineart_fix/work')
import build as B
from r18 import R18
v,outp=sys.argv[1],sys.argv[2]
base_dirs=[d for d in sys.argv[3].split(',') if d]; st_dirs=[d for d in sys.argv[4].split(',') if d]
j=json.load(open(f'{R}/views/{v}/hair/rig.json')); parts=j['parts']; ymax=j.get('swayYMaxPx',0); by={p['id']:p for p in parts}
only=sys.argv[5].split(',') if len(sys.argv)>5 else [p['id'] for p in parts]
def path(dirs,f):
    for d in reversed(dirs):
        if os.path.exists(f'{R}/{d}/views/{v}/hair/{f}'): return f'{d}/views/{v}/hair/{f}'
    return f'views/{v}/hair/{f}'
face=None
for sub in ('eyes','mouth'):
    for f in glob.glob(f'{R}/views/{v}/{sub}/*.png'):
        if any(k in f for k in ('chroma','preview','sheet')): continue
        a=np.array(Image.open(f).convert('RGBA'))[...,3]>0; face=a if face is None else face|a
ys,xs=np.nonzero(face); box=(xs.min()-2,ys.min()-2,xs.max()+3,ys.max()+3); fs=face[box[1]:box[3],box[0]:box[2]]
order=[p for _,p in sorted(enumerate(parts),key=lambda t:(t[1]['layer'],t[0])) if p['id'] in only and p['layer']>=200]
poses=[(f'x={x:+.2f}',{p['id']:tuple(B.lim(q)*x for q in B.chain_of(by,p['id'])) for p in parts}) for x in np.round(np.linspace(-1,1,41),3)]+B.extremes(by,parts)[2:]
r=R18(v); U={}
for tag,dirs in (('baseline',base_dirs),('staged',st_dirs)):
    u=np.zeros(fs.shape,bool)
    for lab,angs in poses:
        for yv in (-1,0,1):
            L=[]
            for p in order:
                A=B.matrix(by,p['id'],angs[p['id']]); dy=int(np.floor(yv*min(1,max(0,p.get('swayY') or 0))*ymax+0.5))
                A=np.array([[1,0,0],[0,1,dy],[0,0,1.0]])@A; L.append((path(dirs,p['file']),B.M6(A)))
            u|=(r.render(L,box)[...,3]>0)&fs
    U[tag]=u
r.close()
res=dict(view=v,quality='linear',parts=only,poses=len(poses)*3,face_px=int(face.sum()),baseline_px_on_face=int(U['baseline'].sum()),staged_px_on_face=int(U['staged'].sum()),new_px_on_face=int((U['staged']&~U['baseline']).sum()))
json.dump(res,open(outp,'w'),indent=1); print(res)
