# Classify NEW see-through px: inside the filled silhouette of the static layers (Body's final base_body/base_body_skin + static
# hair parts, swayWeight 0) = a hole in static coverage; outside it = background legitimately behind a swinging strand edge
# (live showed the frozen hair copy still baked in the live base_body there).
import json,re,numpy as np
from PIL import Image
from scipy import ndimage as nd
L=lambda f:np.array(Image.open(f).convert('RGBA')).astype(int)
R='/workspace/shadowveil'; d=json.load(open('results.json'))
t=open(R+'/rig/index.html').read(); HMAP=json.loads(re.search(r'const HAIRLESS_HAIR=(\{.*?\});',t).group(1))
hp=lambda v,f:R+'/'+HMAP.get(f'../views/{v}/hair/{f}',f'../views/{v}/hair/{f}')[3:]
POSES=[p for p in d['apose'] if isinstance(d['apose'][p],dict) and 'new_px' in d['apose'][p]]
cls={}
for v in d:
    base=L(f'{R}/views/{v}/base.png'); ins=base[...,3]>=250
    bf=(L(f'{R}/body_tools/work/hairless_division_staged/{v}/live_patch_staged/base_body.png')[...,3]>=250)|(L(f'{R}/body_tools/work/hairless_division_staged/{v}/live_patch_staged/base_body_skin.png')[...,3]>=250)
    rig=json.load(open(hp(v,'rig.json')))['parts']; st=np.zeros_like(bf)
    for p in rig:
        if p.get('file') and not (p.get('swayWeight') or 0): st|=L(hp(v,p['file']))[...,3]>=250
    fill=nd.binary_fill_holes(bf|st); fillb=nd.binary_fill_holes(bf)
    c=cls[v]={}
    for p in POSES:
        A=L(f'work/{v}_hairless_{p}.png'); B=L(f'work/{v}_live_{p}.png'); new=ins&(A[...,3]<250)&~(B[...,3]<250)
        hole=new&fill; ys,xs=np.nonzero(hole)
        c[p]=dict(new=int(new.sum()),outside_static_silhouette=int((new&~fill).sum()),inside_static_silhouette=int(hole.sum()),inside_body_only_fill=int((new&fillb).sum()),
                  hole_bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if xs.size else None,hole_xy=[[int(x),int(y)] for x,y in zip(xs,ys)][:60])
    w=max(c,key=lambda p:c[p]['inside_static_silhouette']); print(v,'max inside',w,{k:c[w][k] for k in c[w] if k!='hole_xy'},c[w]['hole_xy'][:30])
json.dump(cls,open('classify.json','w'),indent=1)
