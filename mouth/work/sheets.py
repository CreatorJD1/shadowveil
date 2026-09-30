from PIL import Image, ImageDraw
import numpy as np
OUT='/workspace/shadowveil/mouth'; names=['rest','M','smile','OH','AA','EE']
base=Image.open('front.png').convert('RGBA')
box=(636,262,726,312); Z=6; tw,th=(box[2]-box[0])*Z,(box[3]-box[1])*Z
def sheet(tiles,fn,cols=3):
    rows=(len(tiles)+cols-1)//cols
    S=Image.new('RGB',(cols*tw,rows*(th+24)),(40,40,40)); d=ImageDraw.Draw(S)
    for i,(lab,im) in enumerate(tiles):
        x,y=(i%cols)*tw,(i//cols)*(th+24); S.paste(im,(x,y+24)); d.text((x+6,y+6),lab,fill=(255,255,255))
    S.save(fn)
tiles=[(n,Image.open(f'{OUT}/{n}_chroma.png').crop(box).resize((tw,th),Image.NEAREST)) for n in names]
sheet(tiles,f'{OUT}/review_contact_sheet_chroma.png')
tiles=[('BASE (unmodified)',base.crop(box).convert('RGB').resize((tw,th),Image.LANCZOS))]
for n in names:
    comp=Image.alpha_composite(base.copy(),Image.open(f'{OUT}/{n}.png'))
    tiles.append((n+' on base copy',comp.crop(box).convert('RGB').resize((tw,th),Image.LANCZOS)))
sheet(tiles,f'{OUT}/review_preview_on_face.png',cols=4)
# wider context preview
wb=(600,180,760,340)
row=Image.new('RGB',(160*3*len(names),480))
for i,n in enumerate(names):
    comp=Image.alpha_composite(base.copy(),Image.open(f'{OUT}/{n}.png')).crop(wb).convert('RGB').resize((480,480),Image.LANCZOS)
    row.paste(comp,(i*480,0))
row.save(f'{OUT}/review_preview_face_context.png')
