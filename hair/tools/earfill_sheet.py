import sys; sys.path.insert(0,'/workspace/shadowveil/hair/tools')
from earfill_lib import *
from earfill_regions import EARBOX
from PIL import ImageDraw
Z=5; rows=[]; font=None
def tile(V,sx,hbimg):
    c=unpremul(V.render(sx,0,hair_back=hbimg)); bg=np.full(c.shape[:2]+(3,),255.0); a=c[...,3:]/255
    return (c[...,:3]*a+bg*(1-a)).round().astype(np.uint8)   # renderer canvas background is #fff
for v in VIEWS:
    for k,(x0,y0,x1,y1) in enumerate(EARBOX[v]):
        box=(x0-6,y0-6,x1+6,y1+6); V=View(v,box)
        before=premul(rgba(f'{R}/hair/backup_pre_earfill/{v}/hair_back.png'))
        tiles=[]
        for tag,hb in (('before',before),('after',None)):
            for sx in (-1,0,1):
                t=Image.fromarray(tile(V,sx,hb)).resize(((box[2]-box[0])*Z,(box[3]-box[1])*Z),Image.NEAREST)
                lab=Image.new('RGB',(t.width,18),(30,30,30)); ImageDraw.Draw(lab).text((4,3),f'{v} ear{k+1} {tag} X={sx:+d}',fill=(255,255,255))
                col=Image.new('RGB',(t.width,t.height+18)); col.paste(lab,(0,0)); col.paste(t,(0,18)); tiles.append(col)
        w=sum(t.width for t in tiles)+6*len(tiles); h=max(t.height for t in tiles)
        row=Image.new('RGB',(w,h),(90,90,90)); x=0
        for i,t in enumerate(tiles):
            row.paste(t,(x,0)); x+=t.width+(18 if i==2 else 6)
        rows.append(row)
W=max(r.width for r in rows); Hh=sum(r.height+8 for r in rows)
sheet=Image.new('RGB',(W,Hh),(60,60,60)); y=0
for r in rows: sheet.paste(r,(0,y)); y+=r.height+8
sheet.save('/workspace/shadowveil/hair/ear_fill_sheet.png'); print(sheet.size)
