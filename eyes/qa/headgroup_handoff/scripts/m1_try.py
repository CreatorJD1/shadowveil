import sys,json,numpy as np,cv2
sys.path.insert(0,'scripts'); import eyeseg_copy as S
from PIL import Image
WIN={('apose','EyeR'):(605,195,685,256),('apose','EyeL'):(680,195,762,256),('left','EyeL'):(585,188,655,250),('right','EyeR'):(712,188,788,250)}
def onblue(p):
    a=Image.open(p).convert('RGBA');bg=Image.new('RGBA',a.size,(0,0,255,255));bg.alpha_composite(a);return np.asarray(bg.convert('RGB'))
for (v,e),(x0,y0,x1,y1) in WIN.items():
    out=[]
    for nm,I in [('rig',onblue(f'caps/hg_{v}_rest.png')),('live',onblue(f'caps/live_{v}_rest.png')),('frm',np.asarray(Image.open(f'work/{v}_frame_warped.png')))]:
        c=cv2.cvtColor(np.ascontiguousarray(I[y0:y1,x0:x1]),cv2.COLOR_RGB2BGR)
        m,mk=S.measure(c,e)
        out.append((nm,[round(m['iris_centroid'][0]+x0,1),round(m['iris_centroid'][1]+y0,1)],m['iris_px'],[m['opening_bbox'][0]+x0,m['opening_bbox'][1]+y0,m['opening_bbox'][2]+x0,m['opening_bbox'][3]+y0]))
        vis=c.copy();vis[mk['op']]=(vis[mk['op']]*0.5+np.array([0,0,255])*0.5);vis[mk['ir']]=(0,255,0);vis[mk['lash']]=(255,0,255)
        cv2.imwrite(f'work/seg_{v}_{e}_{nm}.png',cv2.resize(vis,None,fx=6,fy=6,interpolation=cv2.INTER_NEAREST))
    print(v,e,out)
