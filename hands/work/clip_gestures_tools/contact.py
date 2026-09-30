import sys,numpy as np,cv2
sys.path.insert(0,'/workspace/gb'); from tracks import track
from PIL import Image,ImageDraw
VD='/workspace/shadowveil/reference/grok_build/public/clean-room/videos'
K=[('wave','B',12,'wave L f12 open, wave swing (period 11.1 fr)'),('wave','B',93,'wave L f93 curled while lowering'),
   ('point','X560_262',24,'point L f0-63 point pose'),('point','B',69,'point L f69 index releasing'),
   ('stop','A',8,'stop R f8 spread (idx-pinky 43 max)'),('stop','B',8,'stop L f8 spread'),
   ('shrug','B',32,'shrug L open palm'),('inspect','A',4,'inspect R f0-12 claw, palm up'),
   ('inspect','A',60,'inspect R f32-94 soft half-curl'),('inspect','A',116,'inspect R f110-120 curled'),
   ('angry','A',40,'angry R fist f0-144'),('angry','B',40,'angry L fist f0-144'),
   ('ready','A',60,'ready R fist f0-144'),('run','B',42,'run L fist'),('startle','A',42,'startle R f30-60 claw at chest'),('hem','A',36,'hem R f0-72 grip')]
C=180; tiles=[]
cache={}
for c,s,i,lab in K:
    if c not in cache: cache[c]=track(c)
    tr,F=cache[c]
    if s.startswith('X'): x,y=[int(v) for v in s[1:].split('_')]
    else: x,y=tr[s]['x'][i],tr[s]['y'][i]
    S=55; cr=Image.fromarray(F[i]).crop((int(x-S),int(y-S),int(x+S),int(y+S))).resize((C,C),Image.LANCZOS)
    t=Image.new('RGB',(C,C+26),'white'); t.paste(cr,(0,0)); d=ImageDraw.Draw(t); d.text((2,C+1),lab[:34],fill='black'); d.text((2,C+13),lab[34:68],fill='black'); tiles.append(t)
# ours from the real renderer check sheets
def crop_sheet(v,row,col,nrows):
    im=Image.open(f'/workspace/shadowveil/hands/previews/check_{v}.png'); W,H=im.size; top=int(H*0.012); rh=(H-top)/nrows; cw=W/2
    return im.crop((int(col*cw),int(top+row*rh),int((col+1)*cw),int(top+(row+1)*rh)))
for v,row,lab in [('apose',0,'OURS apose L rest (f0)'),('apose',4,'OURS apose L curl 0.5 (f1)'),('apose',1,'OURS apose L Fist (f2)'),('apose',2,'OURS apose L Point'),('tpose',0,'OURS tpose L rest (f0)'),('tpose',4,'OURS tpose L curl 0.5 (f1)'),('tpose',1,'OURS tpose L Fist (f2)'),('tpose',2,'OURS tpose L Point')]:
    cr=crop_sheet(v,row,0,5); cr.thumbnail((C,C)); t=Image.new('RGB',(C,C+26),'white'); t.paste(cr,((C-cr.width)//2,(C-cr.height)//2)); ImageDraw.Draw(t).text((2,C+1),lab,fill='blue'); tiles.append(t)
cols=8; o=Image.new('RGB',(cols*(C+4),((len(tiles)+cols-1)//cols)*(C+30)+22),'white'); d=ImageDraw.Draw(o)
d.text((4,4),'Grok build clips (lossless mp4, 24 fps, 768x1168; crops 110 px -> 180 px) vs our renderer (check_apose/tpose.png). L/R = her side.',fill='black')
for k,t in enumerate(tiles): o.paste(t,((k%cols)*(C+4),22+(k//cols)*(C+30)))
import os; os.makedirs('/workspace/shadowveil/views/apose/hands/previews',exist_ok=True)
o.save('/workspace/shadowveil/views/apose/hands/previews/clip_gestures_ref.png'); print(o.size)
