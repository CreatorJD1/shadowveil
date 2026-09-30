import json,subprocess,numpy as np
from PIL import Image,ImageDraw,ImageFont
I='/workspace/shadowveil/rig/previews/idle';D='data'
rows=[('keys/idle_breathe_left.mp4','idle_breathe','left',144,'smile->rest fade (alpha .83): smile outline still 100% under rest = doubled lip line, 1-2 fr'),
      ('keys/idle_breathe_tpose.mp4','idle_breathe','tpose',81,'rest->smile fade (alpha .56): two seams at ~half strength, 1 fr'),
      ('keys/idle_breathe_apose.mp4','idle_breathe','apose',143,'smile->rest fade start (alpha .28), front'),
      ('keys/idle_weight_shift_left.mp4','idle_weight_shift','left',74,'softest held lip line (-16% edge vs sharp); weight_shift never snaps sharp'),
      ('keys/idle_arm_settle_right.mp4','idle_arm_settle','right',141,'soft frame (rotated, smoothed) just before a sharp snap'),
      ('keys/idle_arm_settle_right.mp4','idle_arm_settle','right',142,'sharp snap frame (head angle exactly 0): lip line pops crisp'),
      ('left_idle.mp4','auto','left',74,'AUTO idle reference: mid-crossfade AA_half->OH (1 of ~48 switches)')]
W,H,S=110,76,3
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
except Exception: font=ImageFont.load_default()
tiles=[]
for path,clip,view,f,note in rows:
    d=json.load(open(f'{D}/mp4_{clip}_{view}.json'));x=d['frames'][f];cx,cy=int(round(x['ax'])),int(round(x['ay']))
    x0,y0=cx-W//2,cy-H//2
    raw=subprocess.run(['ffmpeg','-v','error','-i',f'{I}/{path}','-vf',f'select=eq(n\\,{f}),crop={W}:{H}:{x0}:{y0}','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    fr=Image.fromarray(np.frombuffer(raw,np.uint8).reshape(H,W,3))
    rest=Image.open(f'{I}/frames/{view}/rest.png').convert('RGBA').crop((x0,y0,x0+W,y0+H));bg=Image.new('RGBA',rest.size,(128,128,128,255));bg.alpha_composite(rest);rest=bg.convert('RGB')
    tile=Image.new('RGB',(2*W*S+12,H*S+40),(30,30,30));tile.paste(fr.resize((W*S,H*S),Image.NEAREST),(0,40));tile.paste(rest.resize((W*S,H*S),Image.NEAREST),(W*S+12,40))
    dr=ImageDraw.Draw(tile);dr.text((4,2),f'{path} f{f} t={f/30:.3f}s | right: rest, crop {x0},{y0} {W}x{H}',fill=(255,255,255),font=font)
    dr.text((4,20),note,fill=(255,220,120),font=font);tiles.append(tile)
sheet=Image.new('RGB',(tiles[0].width,sum(t.height+6 for t in tiles)),(0,0,0));y=0
for t in tiles: sheet.paste(t,(0,y));y+=t.height+6
sheet.save('idle_mouth_worst_contact_sheet.png',optimize=True);print(sheet.size)
