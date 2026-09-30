import json; import numpy as np; from PIL import Image, ImageDraw
from zoom import comp
ROOT='/workspace/shadowveil'; Z=4; TW,TH=100,72
def tile(v,n,lab,sub=''):
    a=json.load(open(f'{ROOT}/views/{v}/mouth/rig.json'))['anchor']; ax,ay=a['x'],a['y']
    if v=='left': ax-=10
    if v=='right': ax+=10
    box=(ax-TW//2,ay-44,ax+TW//2,ay-44+TH)
    im=comp(v,n,box,Z) if n else comp(v,None,box,Z)
    d=ImageDraw.Draw(im); d.rectangle([0,0,im.width,15],fill=(0,0,0)); d.text((4,2),lab,fill=(255,255,255))
    if sub: d.rectangle([0,im.height-15,im.width,im.height],fill=(0,0,0)); d.text((4,im.height-13),sub,fill=(255,220,120))
    return im
rows=[]
for v in ['apose','tpose','left','right']:
    t=[tile(v,'rest',f'{v} · rest (live)'),tile(v,'M',f'{v} · M (0,-1) (live)')]
    if v in('apose','tpose'):
        t.append(tile(v,'anger',f'{v} · anger (0.25,-1) LIVE','cut from Clean-room anger art, scale 0.5, rot 0'))
        t.append(Image.new('RGB',t[0].size,(40,40,40)))
        ImageDraw.Draw(t[3]).text((10,10),'front view: no proposal needed',fill=(200,200,200))
    else:
        t.append(tile(v,'M',f'{v} · live at (0.25,-1) = M (fallback)','no side view of the anger face exists'))
        t.append(tile(v,f'{ROOT}/mouth/work/anger/proposal/{v}/anger.png',f'{v} · PROPOSAL - NOT LIVE','front anger mouth squashed x0.26 - not a real profile'))
    rows.append(t)
W,H=rows[0][0].size; G=6
out=Image.new('RGB',(4*W+3*G,4*H+3*G+22),(25,25,25)); d=ImageDraw.Draw(out)
d.text((6,5),'Shadowveil anger mouth v1 - same scale (4x view px) - chroma blue behind her silhouette - 2026-09-30 PT',fill=(255,255,255))
for r,t in enumerate(rows):
    for c,im in enumerate(t): out.paste(im,(c*(W+G),22+r*(H+G)))
out.save('anger_contact_sheet.png'); print(out.size)
# source crop: full anger face (small) + mouth crop with the cut outline
from scipy import ndimage as ndi
from measure import src_mask, SRC
A,L,core=src_mask(); cut=ndi.binary_dilation(core,iterations=1)
src=Image.open(SRC).convert('RGBA'); bg=Image.new('RGBA',src.size,(128,128,128,255)); bg.alpha_composite(src); bg=bg.convert('RGB')
full=bg.resize((352,352),Image.LANCZOS); dr=ImageDraw.Draw(full); dr.rectangle([300/2,380/2,445/2,480/2],outline=(255,255,0))
cr=np.array(bg)[380:480,300:445].copy(); edge=cut^ndi.binary_erosion(cut); e=edge[380:480,300:445]
crA=Image.fromarray(cr).resize((145*4,100*4),Image.NEAREST); crB=cr.copy(); crB[e]=(0,255,0); crB=Image.fromarray(crB).resize((145*4,100*4),Image.NEAREST)
o=Image.new('RGB',(352+145*8+12,400+22),(25,25,25)); o.paste(full,(0,22)); o.paste(crA,(356,22)); o.paste(crB,(356+145*4+6,22))
ImageDraw.Draw(o).text((4,5),'source: reference/grok_build public/puppet/emotions/anger.png (704x704, faces.json kept:anger). Mouth crop x300-445,y380-480 at 4x; right: green = cut boundary (lips + 1px AA rim)',fill=(255,255,255))
o.save('anger_source_crop.png'); print(o.size)
