import sys,json
sys.path.insert(0,'/workspace/shadowveil/hair/qa/idle_battle/tools')
from common import *
from PIL import ImageDraw
Q=P+'/hair/qa/wisp_fix'; os.makedirs(Q+'/crops',exist_ok=True); Z=8
def HM(b): x,y,a=(b.get('head') or b.get('torso')); return T(x-681,y-690.5)@rotAt(681,690.5,a)
def onblue(a):
    al=a[...,3:4]/255.; return (a[...,:3]*al+np.array([0,0,255])*(1-al)).astype(np.uint8)
def amap(a):
    x=a[...,3]; o=np.zeros(x.shape+(3,),np.uint8); o[x==255]=(40,40,40); m=(x<255)&(x>0); o[m,0]=255; o[m,1]=(x[m]).astype(np.uint8); o[x==0]=(0,0,255); return o
def tile(img,label):
    im=Image.fromarray(img).resize((img.shape[1]*Z,img.shape[0]*Z),Image.NEAREST); c=Image.new('RGB',(im.width,im.height+16),(255,255,255)); c.paste(im,(0,16)); ImageDraw.Draw(c).text((3,2),label,fill=(0,0,0)); return c
def row(tiles,fn):
    W=sum(t.width for t in tiles)+4*(len(tiles)-1); H=max(t.height for t in tiles); o=Image.new('RGB',(W,H),(255,255,255)); x=0
    for t in tiles: o.paste(t,(x,0)); x+=t.width+4
    o.save(Q+'/crops/'+fn); print(fn)
cx,cy=630,203; r=16
for clip,new,fr in [('tpose','tpose_idle',20),('keys_idle_weight_shift_tpose','keys_idle_weight_shift_tpose',183)]:
    tiles=[]
    for tag,d in (('before',f'{IDLE}/frames/{clip}'),('after',f'{Q}/render/{new}')):
        F=json.load(open(d+'/meta.json'))['frames']; b=F[fr]['bones']; M=HM(b)
        X,Y,_=M@np.array([cx,cy,1.]); X,Y=int(round(X)),int(round(Y))
        a=np.array(Image.open(f'{d}/frames/f{fr:04d}.png'))[Y-r:Y+r+1,X-r:X+r+1]
        n=int(((a[...,3]<255)).sum())
        tiles+= [tile(onblue(a),f'{tag} f{fr} {b["head"][2]:+.2f}deg on #0000FF'),tile(amap(a),f'{tag} alpha (red=<255) n={n}')]
    row(tiles,f'wisp_{new}_f{fr}_before_after.png')
# rest: hair_back before/after and rest composite
hb0=np.array(Image.open(P+'/hair/backups/wisp_fix_20260930/tpose_hair_back.png').convert('RGBA')); hb1=np.array(Image.open(P+'/views/tpose/hair/hair_back.png').convert('RGBA'))
base=np.array(Image.open(P+'/views/tpose/base.png').convert('RGBA'))
sl=np.s_[cy-r:cy+r+1,cx-r:cx+r+1]
row([tile(onblue(hb0[sl]),'hair_back before (on blue)'),tile(onblue(hb1[sl]),'hair_back after: 320 px fill'),tile(onblue(base[sl]),'base.png (sampled colours)'),
     tile(onblue(np.array(Image.open(P+'/views/tpose/hair/hair_front.png').convert('RGBA'))[sl]),'hair_front (wisp, layer 600)')],'wisp_rest_hair_back_before_after.png')
