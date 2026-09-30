from PIL import Image, ImageDraw
import numpy as np, json, sys
R='/workspace/shadowveil'; names=['rest','M','smile','OH','AA','EE']
views=sys.argv[1:] or ['apose','tpose','left','right']
Z=6; bw,bh=76,50
rowsC=[];rowsP=[]
for v in views:
    rig=json.load(open(f'{R}/views/{v}/mouth/rig.json')); ax,ay=rig['anchor']['x'],rig['anchor']['y']
    if v in('left','right'): cx=ax+(-8 if v=='left' else 8)
    else: cx=ax
    box=(cx-bw//2,ay-20,cx+bw//2,ay-20+bh)
    base=Image.open(f'{R}/views/{v}/base.png').convert('RGBA')
    grey=Image.new('RGBA',base.size,(128,128,128,255)); bg=Image.alpha_composite(grey,base)
    tc=[];tp=[('BASE',bg.crop(box))]
    for n in names:
        tc.append((n,Image.open(f'{R}/mouth/{v}/{n}_chroma.png').convert('RGBA').crop(box)))
        tp.append((n,Image.alpha_composite(bg,Image.open(f'{R}/views/{v}/mouth/{n}.png')).crop(box)))
    rowsC.append((v,tc)); rowsP.append((v,tp))
def sheet(rows,fn):
    cols=max(len(t) for _,t in rows); tw,th=bw*Z,bh*Z
    S=Image.new('RGB',(cols*tw,len(rows)*(th+20)),(30,30,30)); d=ImageDraw.Draw(S)
    for r,(v,t) in enumerate(rows):
        for c,(lab,im) in enumerate(t):
            S.paste(im.convert('RGB').resize((tw,th),Image.LANCZOS),(c*tw,r*(th+20)+20)); d.text((c*tw+5,r*(th+20)+4),f'{v} {lab}',fill=(255,255,255))
    S.save(fn)
sheet(rowsC,f'{R}/mouth/review_v2_contact_sheet_chroma.png')
sheet(rowsP,f'{R}/mouth/review_v2_preview_on_face.png')
