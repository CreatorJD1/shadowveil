import sys; sys.path.insert(0,'/workspace/shadowveil/eyes/tools')
from render_eyes import render
from PIL import Image
v=sys.argv[1]; box=tuple(map(int,sys.argv[2:6])); s=int(sys.argv[6]); out=sys.argv[7]
st=[{},dict(EyeLOpen=.5,EyeROpen=.5),dict(EyeLOpen=0,EyeROpen=0)]
ims=[Image.fromarray(render(v,p)).crop(box).convert('RGB') for p in st]
ims=[i.resize((i.width*s,i.height*s),Image.NEAREST) for i in ims]
sh=Image.new('RGB',(ims[0].width,ims[0].height*3+20),(30,30,30))
for i,t in enumerate(ims): sh.paste(t,(0,i*(t.height+10)))
sh.save(out)
