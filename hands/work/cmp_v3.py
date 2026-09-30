import json,sys
from PIL import Image,ImageDraw
import rigrender2 as R2
ROOT='/workspace/shadowveil'; V=sys.argv[1]; new=sys.argv[2] if len(sys.argv)>2 else f'{ROOT}/hands/work/frames/{V}_v3'
live=f'{ROOT}/views/{V}/hands'
rig=json.load(open(live+'/rig.json'))
boxes=[(h,(d['box'][0]-20,d['box'][1]-10,d['box'][2]+20,d['box'][3]+20)) for h,d in rig['hands'].items() if d.get('visible')]
rows=[('Fist',1),('Fist',.5),('Point',1),('Peace',1)]
s=3; cells=[]
for n,c in rows:
    row=[]
    for lab,dd in (('live',live),('new',new)):
        v={k:x*c for k,x in R2.preset(n).items()}
        im=R2.render(V,v,dd)[0]; bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im)
        for h,b in boxes:
            cc=bg.crop(b).convert('RGB').resize(((b[2]-b[0])*s,(b[3]-b[1])*s),Image.NEAREST); ImageDraw.Draw(cc).text((3,3),f'{lab} {h} {n} {c}',fill='black'); row.append(cc)
    cells.append(row)
cw=max(c.width for r in cells for c in r); ch=max(c.height for r in cells for c in r)
o=Image.new('RGB',(len(cells[0])*(cw+4),len(cells)*(ch+4)),(200,200,200))
for i,r in enumerate(cells):
    for j,c in enumerate(r): o.paste(c,(j*(cw+4),i*(ch+4)))
o.save(f'/tmp/cmp3_{V}.png'); print('ok',V)
