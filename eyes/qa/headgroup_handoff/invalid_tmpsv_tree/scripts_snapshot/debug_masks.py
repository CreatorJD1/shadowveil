import numpy as np
from PIL import Image
Q='/workspace/shadowveil/eyes/qa/headgroup_handoff/'
vis=np.load(Q+'work/vis.npy',allow_pickle=True).item();tiles=[]
for k,d in vis.items():
    x0,y0,x1,y1=d['box']
    for I,m,t in [(d['RG'],d['imR'],d['tmpl']),(d['F'],d['imF'],d['dF'])]:
        c=I[y0:y1,x0:x1].astype(float).copy();mm=m[y0:y1,x0:x1];tt=t[y0:y1,x0:x1]
        c[mm]=c[mm]*0.3+np.array([0,255,0])*0.7;c[tt]=c[tt]*0.3+np.array([255,0,255])*0.7
        tiles.append(Image.fromarray(c.astype(np.uint8)).resize(((x1-x0)*6,(y1-y0)*6),Image.NEAREST))
W=max(t.width for t in tiles)*2+10;H=sum(tiles[i].height+10 for i in range(0,len(tiles),2))
o=Image.new('RGB',(W,H));y=0
for i in range(0,len(tiles),2):o.paste(tiles[i],(0,y));o.paste(tiles[i+1],(tiles[i].width+10,y));y+=tiles[i].height+10
o.save(Q+'work/debug_masks_v4.png')
