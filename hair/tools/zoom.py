import sys; from PIL import Image
from qa_render import BOX
# usage: zoom.py tag view x0,y0,x1,y1(view px) scale out [vals...]
tag,v,box,sc,out=sys.argv[1:6]; vals=sys.argv[6:] or ['-1_0','0_0','1_0']
x0,y0,x1,y1=map(int,box.split(',')); bx,by=BOX[v][:2]; sc=int(sc)
ims=[Image.open(f'/workspace/shadowveil/hair/qa/{tag}_{v}_{s}.png').crop((x0-bx,y0-by,x1-bx,y1-by)) for s in vals]
w,h=ims[0].size; S=Image.new('RGB',(w*len(ims)+3*(len(ims)-1),h),(255,255,255))
for i,x in enumerate(ims): S.paste(x,(i*(w+3),0))
S.resize((S.size[0]*sc,S.size[1]*sc),Image.NEAREST).save(out)
