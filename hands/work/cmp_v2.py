import json,numpy as np,sys
from PIL import Image,ImageDraw
import rigrender as R1, rigrender2 as R2
V='apose'; ROOT='/workspace/shadowveil'
v1dir=f'{ROOT}/hands/work/backup_apose_v2'   # current delivery (v1 procedural frames, rotation 165/165/150)
v2dir=f'{ROOT}/hands/work/frames/apose_v2'
def pose(n,c):
    v=R1.preset('Fist' if n=='Half' else n); cc=c*0.5 if n=='Half' else c
    return {k:x*cc for k,x in v.items()}
def rot_only(v):  # delivered rig without frames (what rotation alone gives)
    rig=json.load(open(f'{v1dir}/rig.json')); out=R1.img(f'{ROOT}/views/{V}/base_body.png').copy(); M=R1.chain(rig,v)
    for p in sorted(rig['parts'],key=lambda p:p['layer']):
        if not p.get('file'): continue
        im=Image.open(f"{v1dir}/{p['file']}").convert('RGBA'); inv=np.linalg.inv(M[p['id']])
        out.alpha_composite(im.convert('RGBa').transform((1365,1739),Image.AFFINE,tuple(inv[0])+tuple(inv[1]),resample=Image.BILINEAR).convert('RGBA'))
    return out
boxes=[(135,645,360,875),(1003,645,1228,875)]
cols=[('rotation only',lambda v:rot_only(v)),('v1 frames',lambda v:R2.render(V,v,v1dir)[0]),('v2 drawn frames',lambda v:R2.render(V,v,v2dir)[0])]
rows=[(n,c) for n in ['Fist','Point','Peace','Half'] for c in ([0.5,1.0] if n!='Half' else [1.0])]
s=2; cw=225*s; ch=230*s
o=Image.new('RGB',(len(cols)*2*(cw+4)+4,len(rows)*(ch+4)+24),(210,210,210)); d=ImageDraw.Draw(o)
for j,(cn,_) in enumerate(cols): d.text((4+j*2*(cw+4)+10,6),cn+'  (her R | her L)',fill='black')
for i,(n,c) in enumerate(rows):
    v=pose(n,c)
    for j,(cn,f) in enumerate(cols):
        im=f(v); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im)
        for k,b in enumerate(boxes):
            cell=bg.crop(b).resize((cw,ch),Image.NEAREST).convert('RGB'); dd=ImageDraw.Draw(cell); dd.text((3,3),f'{n} {c}',fill='black')
            o.paste(cell,(4+(j*2+k)*(cw+4),24+i*(ch+4)))
o.save(f'{ROOT}/hands/work/frames/apose_rotation_vs_frames_v2.png'); print('ok')
