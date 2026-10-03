import numpy as np, json
from PIL import Image, ImageDraw
R='/workspace/shadowveil/'; D=R+'hands/staged/f5_lineart/v2_ring_width/'
def zoom(a,box,s=8):
    im=Image.fromarray(a.astype(np.uint8),'RGBA'); bg=Image.new('RGBA',im.size,(0,0,255,255)); bg.alpha_composite(im); return bg.crop(box).resize(((box[2]-box[0])*s,(box[3]-box[1])*s),Image.NEAREST).convert('RGB')
BOX={'L':(250,780,292,830),'R':(1072,780,1114,830)}
for S in 'LR':
    rows=[]
    # frame file row: live f1 / v1 / v2
    fr=[np.array(Image.open(p+f'{S}_Ring1_f1.png').convert('RGBA')) for p in (R+'views/back/hands/',R+'hands/staged/f5_lineart/back/',D+'back/')]
    rows.append(('Ring1_f1 file: live | F5 v1 | v2',[zoom(a,BOX[S],6) for a in fr]))
    for c in ('curl_0.13','curl_0.20'):
        ims=[np.array(Image.open(f'r_{n}_linear/{c}.png').convert('RGBA')) for n in ('live2','v1','final')]
        rows.append((f'render {c} (rig, linear): live | F5 v1 | v2',[zoom(a,BOX[S],6) for a in ims]))
    W=sum(t.width for t in rows[0][1])+40; H=sum(r[1][0].height+24 for r in rows)+10
    out=Image.new('RGB',(W,H),(30,30,30)); d=ImageDraw.Draw(out); y=5
    for t,tl in rows:
        d.text((5,y),t,fill=(255,255,255)); x=5
        for im in tl: out.paste(im,(x,y+16)); x+=im.width+15
        y+=tl[0].height+24
    out.save(D+f'sheets/back_{S}_Ring1_v2.png'); print(out.size)
