import numpy as np,sys
from PIL import Image
Q='/workspace/shadowveil/eyes/qa/headgroup_handoff/'
vis=np.load(Q+'work/vis.npy',allow_pickle=True).item()
for k,d in vis.items():
    tiles=[]
    for I,o in [(d['RG'],d['oR']),(d['F'],d['oF'])]:
        ys,xs=np.nonzero(o['band']);x0,y0,x1,y1=xs.min()-6,ys.min()-8,xs.max()+7,ys.max()+20
        c=I[y0:y1,x0:x1].astype(float).copy()
        for m,col,al in [(o['band'],(255,0,255),0.5),(o['roi'],(0,160,255),0.35),(o['iris'],(0,255,0),0.6)]:
            mm=m[y0:y1,x0:x1];c[mm]=c[mm]*(1-al)+np.array(col)*al
        tiles.append(Image.fromarray(c.astype(np.uint8)).resize(((x1-x0)*8,(y1-y0)*8),Image.NEAREST))
    o=Image.new('RGB',(tiles[0].width+tiles[1].width+10,max(t.height for t in tiles)));o.paste(tiles[0],(0,0));o.paste(tiles[1],(tiles[0].width+10,0))
    o.save(Q+f'work/dbgopen_{k}.png')
