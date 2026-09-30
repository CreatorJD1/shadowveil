# owner map: which hand layer is topmost (alpha>=100) per pixel, next to the composite, zoomed. ownermap.py <dir> <side> box scale out cases...
import numpy as np,json,sys
from PIL import Image,ImageDraw
D,S,box,sc,out=sys.argv[1],sys.argv[2],tuple(map(int,sys.argv[3].split(','))),int(sys.argv[4]),sys.argv[5]; cases=sys.argv[6:]
meta=json.load(open(D+'/meta.json'));C={c['name']:c for c in meta['cases']}
COL={'palm':(255,255,255),'Thumb':(255,0,255),'Index':(255,60,60),'Middle':(60,200,60),'Ring':(60,120,255),'Pinky':(255,200,0)}
x0,y0,x1,y1=box;w,h=(x1-x0)*sc,(y1-y0)*sc
sh=Image.new('RGB',(2*w,len(cases)*(h+14)),(30,30,30));d=ImageDraw.Draw(sh)
for r,cn in enumerate(cases):
    fin=Image.open(f'{D}/{cn}.png').crop(box);g=Image.new('RGBA',fin.size,(128,128,128,255));g.alpha_composite(fin)
    om=np.zeros((y1-y0,x1-x0,3),np.uint8)+40
    ps=sorted([k for k in C[cn]['parts'] if k.startswith(S+'_')],key=lambda k:C[cn]['parts'][k]['layer'])
    for p in ps:
        a=np.array(Image.open(f'{D}/{cn}_layers/{p}.png').crop(box)).astype(int);m=a[...,3]>=100
        f=[k for k in COL if k in p][0];seg=p[-1] if p[-1].isdigit() else '0';c=np.array(COL[f])*(1.0 if seg in'0' else {'1':1.0,'2':0.7,'3':0.45}[seg])
        dk=m&(a[...,:3].sum(-1)<250)
        om[m]=c.astype(np.uint8);om[dk]=(c*0.35).astype(np.uint8)
    y=r*(h+14);d.text((3,y),cn,fill=(230,230,230))
    sh.paste(g.convert('RGB').resize((w,h),Image.NEAREST),(0,y+14));sh.paste(Image.fromarray(om).resize((w,h),Image.NEAREST),(w,y+14))
sh.save(out);print(out,sh.size)
