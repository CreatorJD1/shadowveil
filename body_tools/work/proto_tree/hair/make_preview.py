import json, numpy as np, colorsys
from PIL import Image, ImageDraw
R='/workspace/shadowveil'; VIEWS=['apose','tpose','left','right','back']
X0,Y0,X1,Y1=500,20,870,370; S=2
tiles=[]
for v in VIEWS:
    base=np.array(Image.open(f'{R}/views/{v}/base.png').convert('RGBA')).astype(int)
    rgb=np.where(base[...,3:]>0,base[...,:3],255); vis=(rgb*0.35+255*0.65)
    rig=json.load(open(f'{R}/views/{v}/hair/rig.json'))
    cols={}; n=len([e for e in rig if e['id'].startswith('strand')])
    for e in rig:
        a=np.array(Image.open(f"{R}/views/{v}/hair/{e['file']}"))[...,3]>0
        if e['id']=='hair_back': c=(150,150,150); a=a&(base[...,3]==0)|a&~(base[...,3]>0)  # fill only visible where base empty
        elif e['id']=='hair_front': c=(60,60,60)
        elif e['id']=='bun': c=(230,140,0)
        else:
            k=int(e['id'].split('_')[1])-1; c=tuple(int(255*t) for t in colorsys.hsv_to_rgb((k/max(n,1))*0.8+0.55,0.9,0.95))
        if e['id']!='hair_back': vis[a]=c
        cols[e['id']]=c
    if v=='back':
        hb=np.array(Image.open(f'{R}/views/{v}/hair/hair_back.png'))[...,3]>0
        hf=(hb)&~np.any([np.array(Image.open(f"{R}/views/{v}/hair/{e['file']}"))[...,3]>0 for e in rig if e['id']!='hair_back'],0)
        vis[hf]=(60,60,60); cols['hair_back (cap)']=(60,60,60)
    im=Image.fromarray(vis[Y0:Y1,X0:X1].astype(np.uint8)).resize(((X1-X0)*S,(Y1-Y0)*S),Image.NEAREST)
    d=ImageDraw.Draw(im)
    for e in rig:
        if e['swayWeight']<=0: continue
        x,y=(e['pivotX']-X0)*S,(e['pivotY']-Y0)*S; c=cols[e['id']]
        d.ellipse([x-6,y-6,x+6,y+6],outline=(0,0,0),width=2,fill=(255,255,255)); d.line([x-9,y,x+9,y],fill=(0,0,0)); d.line([x,y-9,x,y+9],fill=(0,0,0))
        d.text((x+8,y-14),f"{e['id'].replace('strand_','s')} {e['maxSwayDeg']:g}°",fill=(0,0,0))
    d.rectangle([0,0,im.size[0]-1,24],fill=(255,255,255)); d.text((6,6),f"{v}: grey=hair_front/cap  orange=bun  colours=strands  o=pivot (maxSwayDeg)",fill=(0,0,0))
    tiles.append(im)
W=sum(t.size[0] for t in tiles); H=tiles[0].size[1]
sheet=Image.new('RGB',(W,H),(255,255,255)); x=0
for t in tiles: sheet.paste(t,(x,0)); x+=t.size[0]
sheet.save(f'{R}/hair/preview.png'); print(sheet.size)
