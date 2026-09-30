import json, numpy as np
from PIL import Image, ImageDraw
S=json.load(open('turn_stats.json')); rows=S['rows']; P=json.load(open('tmp/pass1.json'))
th=np.array([d['theta'] for d in rows])
FR='/workspace/shadowveil/reference/apose_turn/frames/f%03d.png'
# 5-degree steps: nearest frame to each target (moving part of the turn only: first 0 at f001, 360 end at the first frame reaching it)
picks=[]
for t in range(0,360,5):
    i=int(np.argmin(np.abs(((th-t)+180)%360-180))); picks.append((t,i))
# mouth position for hidden frames: keep the seam height, x from the head-centre track (offset learned on visible frames)
off=np.median([d['mouthCx']-P[j]['headCx'] for j,d in enumerate(rows) if d['visible']])
TW,THh=192,128; tiles=[]
for t,i in picks:
    d=rows[i]; a=Image.open(FR%(i+1)).convert('RGB')
    cx=d['mouthCx'] if d['visible'] else P[i]['headCx']+off; cy=d['seamY'] if d['visible'] else S['SEAM0']
    im=a.crop((int(cx-24),int(cy-16),int(cx+24),int(cy+16))).resize((TW,THh),Image.LANCZOS); D=ImageDraw.Draw(im)
    D.rectangle([0,0,TW,24],fill=(0,0,0))
    D.text((3,1),'%s  %.0f deg (target %d)'%(d['frame'],d['theta'],t),fill=(255,255,0))
    if d['visible']:
        D.text((3,12),'W %.1fpx %s %s %s'%(d['W_px'],'closed' if d['closed'] else 'OPEN','2 corners' if d['bothCornersVisible'] else '1 corner',d['crisp']),fill=(200,255,200))
    else: D.text((3,12),'mouth not visible',fill=(255,160,160))
    tiles.append(im)
cols=8; nr=int(np.ceil(len(tiles)/cols))
sheet=Image.new('RGB',(cols*TW,nr*THh+30),(20,20,20)); D=ImageDraw.Draw(sheet)
D.text((6,4),'apose-turn.mp4 (Coder frames f001-f241, 768x1168): mouth crops 48x32 src px, 4x. Angle: 0 front, 90 facing screen-left (= our left view), 180 back, 270 facing screen-right (= our right view).',fill=(255,255,255))
D.text((6,16),'Angle from arm-span keyframes (profiles f060/f159, back f108.5), face cue near front. W = mouth width in source px.',fill=(200,200,200))
for k,im in enumerate(tiles): sheet.paste(im,((k%cols)*TW,30+(k//cols)*THh))
sheet.save('turn_mouth_contact_sheet.png'); print(sheet.size, [(t,rows[i]['frame']) for t,i in picks])
