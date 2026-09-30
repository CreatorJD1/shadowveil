# crop sheet: sheet.py out.png box(x0,y0,x1,y1) scale dir1:name1,name2,... [dir2:...]  (rows = dirs)
import sys
from PIL import Image,ImageDraw
out,box,S=sys.argv[1],tuple(map(int,sys.argv[2].split(','))),float(sys.argv[3]); rows=[a.split(':') for a in sys.argv[4:]]
w,h=int((box[2]-box[0])*S),int((box[3]-box[1])*S); lab=16
cols=max(len(r[1].split(',')) for r in rows)
sh=Image.new('RGB',(cols*w,len(rows)*(h+lab)),(40,40,44)); d=ImageDraw.Draw(sh)
for i,(dr,names) in enumerate(rows):
    for j,n in enumerate(names.split(',')):
        im=Image.open(f'{dr}/{n}.png').crop(box); g=Image.new('RGBA',im.size,(128,128,128,255)); g.alpha_composite(im)
        sh.paste(g.convert('RGB').resize((w,h),Image.NEAREST),(j*w,i*(h+lab)+lab)); d.text((j*w+3,i*(h+lab)+2),f'{dr.split("renders/")[-1]} {n}',fill=(230,230,230))
sh.save(out); print(out,sh.size)
