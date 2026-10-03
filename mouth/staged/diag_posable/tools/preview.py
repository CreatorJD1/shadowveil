import numpy as np, json, sys
from PIL import Image
d=json.load(open('build_log.json')); t=sys.argv[1]; fr={'045':33,'315':191}[t]
ref=np.asarray(Image.open(f'/workspace/shadowveil/reference/apose_turn/frames/f{fr:03d}.png').convert('RGB'))
x0,y0,x1,y1=d[t]['_tones']['frame_box']; x0+=8;x1-=8;y0+=8;y1-=12
names=['rest','M','smile','OH_half','AA_half','EE_half','OH','AA','EE']
rows=[]
for r in range(3):
    tiles=[]
    for n in names[r*3:r*3+3]:
        p=np.asarray(Image.open(f'{t}/frame_scale/{n}.png'))
        c=np.where(p[...,3:4]==255,p[...,:3],ref)[y0:y1,x0:x1]
        tiles+= [np.kron(c,np.ones((10,10,1),np.uint8)), np.full((c.shape[0]*10,6,3),255,np.uint8)]
    rows+= [np.concatenate(tiles,1), np.full((6,np.concatenate(tiles,1).shape[1],3),255,np.uint8)]
Image.fromarray(np.concatenate(rows,0)).save(f'tools/preview/prev_{t}.png')
