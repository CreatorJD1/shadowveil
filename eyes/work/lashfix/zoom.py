import sys,json,numpy as np
sys.path.insert(0,'/workspace/shadowveil/eyes/tools')
import render_eyes
from PIL import Image
v,root,tag,box=sys.argv[1],sys.argv[2],sys.argv[3],[int(x) for x in sys.argv[4].split(',')]
ks=[int(x) for x in sys.argv[5].split(',')]; z=int(sys.argv[6]) if len(sys.argv)>6 else 10
render_eyes.VIEWS=root
x0,y0,x1,y1=box; rows=[]
for k in ks:
    o=1-k/7
    im=render_eyes.render(v,dict(EyeLOpen=o,EyeROpen=o),base=f'/workspace/shadowveil/views/{v}/base.png')[y0:y1,x0:x1,:3]
    rows.append(im); rows.append(np.full((1,im.shape[1],3),255,np.uint8))
g=np.concatenate(rows,0)
Image.fromarray(g).resize((g.shape[1]*z,g.shape[0]*z),Image.NEAREST).save(f'tmp/{tag}.png')
