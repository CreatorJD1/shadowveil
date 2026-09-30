import sys,json,numpy as np
sys.path.insert(0,'/workspace/shadowveil/eyes/tools')
import render_eyes
from PIL import Image
v=sys.argv[1]; root=sys.argv[2]; tag=sys.argv[3]; ks=[int(x) for x in sys.argv[4].split(',')] if len(sys.argv)>4 else range(8)
render_eyes.VIEWS=root
rig=json.load(open(f'{root}/{v}/eyes/rig.json'))
x0,y0,x1,y1=rig['workRegion']
rows=[]
for k in ks:
    o=1-k/7
    im=render_eyes.render(v,dict(EyeLOpen=o,EyeROpen=o),base=f'/workspace/shadowveil/views/{v}/base.png')[y0:y1,x0:x1,:3]
    rows.append(im); rows.append(np.full((2,im.shape[1],3),255,np.uint8))
g=np.concatenate(rows,0)
Image.fromarray(g).resize((g.shape[1]*5,g.shape[0]*5),Image.NEAREST).save(f'tmp/{tag}_{v}.png')
