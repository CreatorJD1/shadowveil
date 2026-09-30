from rigrender import *
import sys
v=sys.argv[1] if len(sys.argv)>1 else 'apose'
FD=f'{ROOT}/hands/work/frames/{v}'
poses={'Fist':preset('Fist'),'Point':preset('Point'),'Peace':preset('Peace'),'HalfCurl':{f'Hand{h}{f}':0.5 for h in 'LR' for f in FING}}
rows=[]
for pn,pv in poses.items():
    cells=[]
    for mode in ['rotation only','rotation + frames']:
        im,rig=render(v,pv,framesdir=(FD if 'frames' in mode else None))
        bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); bg=bg.convert('RGB')
        for h,b in hand_boxes(rig):
            c=bg.crop(b).resize(((b[2]-b[0])*3,(b[3]-b[1])*3),Image.NEAREST)
            d=ImageDraw.Draw(c); d.rectangle([0,0,c.size[0],14],fill='white'); d.text((3,2),f'{v} {h} {pn}: {mode}',fill='black'); cells.append(c)
    rows.append(cells)
Wc=sum(c.size[0] for c in rows[0])+6*(len(rows[0])+1); Hc=max(c.size[1] for c in rows[0])
o=Image.new('RGB',(Wc,len(rows)*(Hc+6)+6),(200,200,200))
for r,cells in enumerate(rows):
    x=6
    for c in cells: o.paste(c,(x,6+r*(Hc+6))); x+=c.size[0]+6
o.save(f'{ROOT}/hands/work/frames/{v}_rotation_vs_frames.png'); print(o.size)
