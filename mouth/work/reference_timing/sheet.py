import json, csv, numpy as np
from PIL import Image, ImageDraw
TW,TH=240,156
rows=list(csv.DictReader(open('reference_mouth_frames.csv')))
st=json.load(open('reference_stats.json'))
def her(clip,frame):
    c=np.load(f'tmp/{clip}_crops.npy',mmap_mode='r'); a=np.array(c[frame]); a=a[:,:a.shape[1]//2]
    return Image.fromarray(a).resize((TW,TH),Image.LANCZOS)
def lab(im,t1,t2='',col=(255,255,0)):
    d=ImageDraw.Draw(im); d.rectangle([0,0,TW,26],fill=(0,0,0)); d.text((3,1),t1,fill=col); d.text((3,13),t2,fill=(220,220,220)); return im
def R(clip,frame): return next(x for x in rows if x['clip']==clip and int(x['frame'])==frame)
tiles=[]
# row block 1: our 9 shapes (apose, composited on base; crop scaled so rest width matches her tiles)
V='/workspace/shadowveil/views/apose'; rig=json.load(open(f'{V}/mouth/rig.json')); ax,ay=rig['anchor']['x'],rig['anchor']['y']
base=Image.open(f'{V}/base.png').convert('RGBA')
sc=48/(34.2/80)   # our rest W 48 px shown at the same fraction of tile width as her rest (34.2 of 80 video px)
ow,oh=int(sc),int(sc*TH/TW)
ours=[]
for n in ['rest','M','smile','OH_half','AA_half','EE_half','OH','AA','EE']:
    im=base.copy(); im.alpha_composite(Image.open(f'{V}/mouth/{n}.png').convert('RGBA'))
    t=im.crop((ax-ow//2,ay-oh//2+2,ax+ow//2,ay+oh//2+2)).convert('RGB').resize((TW,TH),Image.LANCZOS)
    o=st['ours'][n]; ours.append(lab(t,'OURS '+n,'w %.2f o %.2f lift %.2f'%(o['w'],o['o'],o['lift']),(120,255,120)))
# row block 2: her talk, one tile per drawing (middle frame), first 18 drawings
T=[x for x in rows if x['clip']=='talk']; d=[0]+[i for i in range(1,len(T)) if float(T[i]['frameDiff'])>8]
talk=[]
for k,s in enumerate(d[:18]):
    f=s+1 if s+1<len(T) else s; x=T[f]
    talk.append(lab(her('talk',f),'talk f%d %dms -> %s'%(f,round(float(x['t_ms'])),x['shape']),'w %.2f o %.2f lift %.2f'%(float(x['w']),float(x['o']),float(x['lift']))))
# row block 3: key frames from the other clips
def pick(clip,key,fn=max):
    xs=[x for x in rows if x['clip']==clip]; return int(fn(xs,key=lambda x:float(x[key]))['frame'])
keys=[('idle',50,'rest (idle)'),('idle-long',70,'soft smile'),('smirk',120,'smirk: closed smile'),('tongue',110,'wide teeth grin'),
      ('tongue',60,'tongue out'),('talk',pick('talk','teeth_px'),'talk teeth grin'),('talk',pick('talk','o'),'talk max open'),
      ('gasp',pick('gasp','o'),'gasp: round O max'),('startle',30,'startle'),('glare',70,'glare: pressed'),('angry',70,'angry: pressed'),('worry',100,'worry')]
extra=[]
for c,f,t in keys:
    x=R(c,f); extra.append(lab(her(c,f),'%s f%d: %s'%(c,f,t),'w %.2f o %.2f lift %.2f teeth %s'%(float(x['w']),float(x['o']),float(x['lift']),x['teeth_px'])))
allt=ours+talk+extra; cols=9
nrow=int(np.ceil(len(allt)/cols))
S=Image.new('RGB',(cols*TW,nrow*TH+40),(30,30,30)); D=ImageDraw.Draw(S)
D.text((6,6),'Reference mouth measurement (Grok clean-room mp4s, 24 fps). Row 1: our apose shapes. Rows 2-3: talk, one tile per held drawing (~125 ms). Rows 4-5: key frames. w=width/rest width, o=opening/rest width, lift=corner lift/rest width.',fill=(255,255,255))
D.text((6,22),'Her tiles: 4x bicubic upscale of ~80x52 video px (low-res AI video). Tiles scaled so her rest width and our rest width occupy the same fraction of the tile.',fill=(200,200,200))
for i,t in enumerate(allt): S.paste(t,((i%cols)*TW,40+(i//cols)*TH))
S.save('reference_contact_sheet.png'); print(S.size)
