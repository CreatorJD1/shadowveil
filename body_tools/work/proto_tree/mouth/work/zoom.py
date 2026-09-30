from PIL import Image, ImageDraw
import sys
R='/workspace/shadowveil'; names=['rest','M','smile','OH_half','AA_half','EE_half','OH','AA','EE']
tag=sys.argv[1]
B={'right':(748,252,796,300),'left':(576,248,624,296),'apose':(649,266,713,310),'tpose':(650,257,714,301)}
for v,box in B.items():
  base=Image.open(f'{R}/views/{v}/base.png').convert('RGBA'); bg=Image.alpha_composite(Image.new('RGBA',base.size,(128,128,128,255)),base)
  w,h=box[2]-box[0],box[3]-box[1]; z=6
  S=Image.new('RGB',(3*w*z,3*h*z)); d=ImageDraw.Draw(S)
  for i,n in enumerate(names):
    t=Image.alpha_composite(bg,Image.open(f'{R}/views/{v}/mouth/{n}.png')).crop(box).resize((w*z,h*z),Image.NEAREST); S.paste(t.convert('RGB'),((i%3)*w*z,(i//3)*h*z)); d.text(((i%3)*w*z+4,(i//3)*h*z+4),n,fill=(255,255,255))
  S.save(f'{tag}_{v}.png')
