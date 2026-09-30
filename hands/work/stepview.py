from PIL import Image
from rigrender2 import render,preset
import sys
d=sys.argv[1]
ims=[]
for v in [preset('Fist'),{k:x*0.75 for k,x in preset('Fist').items()},{k:x*0.5 for k,x in preset('Fist').items()}]:
  im=render('apose',v,d)[0]; bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im)
  ims.append(bg.crop((195,680,265,730)).resize((350,250),Image.NEAREST)); ims.append(bg.crop((1098,680,1168,730)).resize((350,250),Image.NEAREST))
o=Image.new('RGB',(710,770),'gray')
for i,m in enumerate(ims): o.paste(m,((i%2)*360,(i//2)*260))
o.save('/tmp/step.png')
