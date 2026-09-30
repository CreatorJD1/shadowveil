import sys; sys.path.insert(0,'/workspace/shadowveil/eyes/tools')
from render_eyes import render
from PIL import Image, ImageDraw
import numpy as np
v=sys.argv[1]; box=tuple(map(int,sys.argv[2:6])); s=int(sys.argv[6]); out=sys.argv[7]
st=[{},dict(EyeLOpen=.75,EyeROpen=.75),dict(EyeLOpen=.5,EyeROpen=.5),dict(EyeLOpen=.25,EyeROpen=.25),dict(EyeLOpen=0,EyeROpen=0),dict(EyeBallX=1,EyeBallY=1),dict(EyeBallX=-1,EyeBallY=-1),dict(EyeBallX=1),dict(EyeBallY=1)]
tiles=[]
for p in st:
    im=Image.fromarray(render(v,p)).crop(box).convert('RGB'); tiles.append(im.resize((im.width*s,im.height*s),Image.NEAREST))
w,h=tiles[0].size; sh=Image.new('RGB',(w*3+20,h*3+20),(30,30,30))
for i,t in enumerate(tiles): sh.paste(t,((i%3)*(w+10),(i//3)*(h+10)))
sh.save(out)
