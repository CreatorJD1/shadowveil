import json
from PIL import Image,ImageDraw
S=3
cols=[('arm_settle_f071',(1080,520,1290,730)),('weight_shift_f182',(1140,300,1345,480)),('breathe_f123_liftpeak',(1150,340,1345,480))]
rows=[('BEFORE live (hold 0.3/0.5/0.5/0.55)','renders/fix_keys/tpose','_before'),('AFTER keys: viewKeys.tpose finger curls x0.32','renders/fix_keys/tpose','_after'),('AFTER keys + scratch frames [f0,f1,f1,f1,f2]','renders/fix_keys_frames5/tpose','_after')]
W=sum((b[2]-b[0])*S for _,b in cols);Hs=[max((b[3]-b[1])*S for _,b in cols)]
h=Hs[0];sh=Image.new('RGB',(W,len(rows)*(h+18)+20),(35,35,38));d=ImageDraw.Draw(sh)
d.text((4,4),'tpose L hand, rig/index.html render path (unchanged), scratch data only',fill=(255,255,255))
for r,(lab,dr,suf) in enumerate(rows):
    x=0;y=20+r*(h+18);d.text((4,y+2),lab,fill=(255,230,120))
    for cn,b in cols:
        im=Image.open(f'{dr}/{cn}{suf}.png').crop(b);g=Image.new('RGBA',im.size,(128,128,128,255));g.alpha_composite(im)
        sh.paste(g.convert('RGB').resize(((b[2]-b[0])*S,(b[3]-b[1])*S),Image.LANCZOS),(x,y+16));d.text((x+4,y+h+2),cn,fill=(200,200,200));x+=(b[2]-b[0])*S
sh.save('tpose_before_after.png');print(sh.size)
