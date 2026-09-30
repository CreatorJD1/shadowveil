import json,numpy as np,sys
from PIL import Image,ImageDraw
import rigrender as R1, rigrender2 as R2
V=sys.argv[1]; ROOT='/workspace/shadowveil'
old=f'{ROOT}/hands/work/backup_v2/{V}'; new=f'{ROOT}/hands/work/frames/{V}_v2'
def pose(n,c):
    v=R1.preset('Fist' if n=='Half' else n); cc=c*0.5 if n=='Half' else c
    return {k:x*cc for k,x in v.items()}
rig=json.load(open(old+'/rig.json'))
boxes=[(h,(b[0]-30,b[1]-30,b[2]+30,b[3]+30)) for h,d in rig['hands'].items() if d.get('visible') for b in [d['box']]]
cols=[('rotation only',old),('v2 drawn frames',new)]
rows=[('Fist',.5),('Fist',1),('Point',1),('Peace',1),('Half',1)]
s=2; bw=max(b[2]-b[0] for _,b in boxes)*s; bh=max(b[3]-b[1] for _,b in boxes)*s
o=Image.new('RGB',(len(cols)*len(boxes)*(bw+4)+4,len(rows)*(bh+4)+24),(210,210,210)); d=ImageDraw.Draw(o)
for j,(cn,_) in enumerate(cols): d.text((4+j*len(boxes)*(bw+4)+10,6),f'{V}: {cn}',fill='black')
for i,(n,c) in enumerate(rows):
    for j,(cn,hd) in enumerate(cols):
        im=R2.render(V,pose(n,c),hd)[0]; bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im)
        for k,(h,b) in enumerate(boxes):
            cell=bg.crop(b).resize(((b[2]-b[0])*s,(b[3]-b[1])*s),Image.NEAREST).convert('RGB'); ImageDraw.Draw(cell).text((3,3),f'{h} {n} {c}',fill='black')
            o.paste(cell,(4+(j*len(boxes)+k)*(bw+4),24+i*(bh+4)))
o.save(f'{ROOT}/hands/work/frames/{V}_rotation_vs_frames_v2.png'); print('ok',V)
