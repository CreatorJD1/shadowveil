import json,numpy as np
from PIL import Image
R='/workspace/shadowveil/'
H=json.load(open(R+'body_tools/work/apose_turn/angle_map.json'))['handoff']
def onwhite(p):
    a=Image.open(p).convert('RGBA');bg=Image.new('RGBA',a.size,(0,0,255,255));bg.alpha_composite(a);return bg.convert('RGB')
for v,box in [('apose',(590,170,780,280)),('left',(560,160,690,270)),('right',(690,160,820,270))]:
    h=H[v];s=h['scale']
    fr=Image.open(R+f"reference/apose_turn/frames/f{h['frame']:03d}.png").convert('RGB')
    F=fr.transform((1365,1739),Image.AFFINE,(1/s,0,-h['dx']/s,0,1/s,-h['dy']/s),resample=Image.BICUBIC)
    F.save(f'work/{v}_frame_warped.png')
    L=onwhite(f'caps/hg_{v}_rest.png')
    w=box[2]-box[0];hh=box[3]-box[1]
    out=Image.new('RGB',(w*4*2+10,hh*4))
    out.paste(L.crop(box).resize((w*4,hh*4),Image.NEAREST),(0,0));out.paste(F.crop(box).resize((w*4,hh*4),Image.NEAREST),(w*4+10,0))
    out.save(f'work/peek_{v}.png')
