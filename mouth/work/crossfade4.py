# 50% crossfade exactly as rig/index.html draws it: base, then outgoing at globalAlpha 0.5, then incoming at 0.5 (same layer).
from PIL import Image, ImageDraw
import numpy as np, json
from lipmask import load, lip_mask
GUESS={'apose':(681,289),'tpose':(684,281),'left':(609,285),'right':(774,272)}
R='/workspace/shadowveil'
PAIRS=[('rest','AA'),('rest','smile'),('AA','EE'),('M','OH'),('rest','AA_half'),('AA_half','AA')]
Z=6; bw,bh=76,50
def half(im,a):
    x=np.array(im).astype(float); x[...,3]*=a; return Image.fromarray(np.round(x).astype(np.uint8),'RGBA')
rows=[]; stats={}
for v in ['apose','tpose','left','right']:
    rig=json.load(open(f'{R}/views/{v}/mouth/rig.json')); ax,ay=rig['anchor']['x'],rig['anchor']['y']
    cx=ax+(-8 if v=='left' else 8 if v=='right' else 0); box=(cx-bw//2,ay-20,cx+bw//2,ay-20+bh)
    base=Image.open(f'{R}/views/{v}/base.png').convert('RGBA')
    bg=Image.alpha_composite(Image.new('RGBA',base.size,(128,128,128,255)),base)
    Dm=lip_mask(load(v),*GUESS[v],profile=v in('left','right'))[1]
    P={n:Image.open(f'{R}/views/{v}/mouth/{n}.png') for n in set(sum(map(list,PAIRS),[]))}
    tiles=[]
    for a,b in PAIRS:
        f=Image.alpha_composite(Image.alpha_composite(bg,half(P[a],0.5)),half(P[b],0.5))
        tiles.append((f'{v} {a}->{b} @50%',f.crop(box)))
        # ghost metric: renderer midframe vs ideal 50/50 mix of the two finished shapes, on her drawn-lip pixels
        Bf=np.array(bg).astype(float)
        fa=np.array(Image.alpha_composite(bg,P[a])).astype(float); fb=np.array(Image.alpha_composite(bg,P[b])).astype(float)
        ideal=0.5*fa+0.5*fb; mid=np.array(f).astype(float)
        dd=np.abs(mid-ideal)[...,:3].max(-1)[Dm]
        pa=np.array(P[a])[...,3]/255; pb=np.array(P[b])[...,3]/255
        stats[f'{v} {a}->{b}']=dict(baseShowThroughOnLips=round(float(((1-0.5*pa)*(1-0.5*pb))[Dm].max()),3),
                                    maxDevFromIdealMix=int(dd.max()),meanDevFromIdealMix=round(float(dd.mean()),2))
    rows.append(tiles)
tw,th=bw*Z,bh*Z; cols=len(PAIRS)
S=Image.new('RGB',(cols*tw,len(rows)*(th+20)),(30,30,30)); d=ImageDraw.Draw(S)
for r,t in enumerate(rows):
    for c,(lab,im) in enumerate(t):
        S.paste(im.convert('RGB').resize((tw,th),Image.LANCZOS),(c*tw,r*(th+20)+20)); d.text((c*tw+5,r*(th+20)+4),lab,fill=(255,255,255))
S.save(f'{R}/mouth/review_v4_crossfade_50.png')
json.dump(stats,open(f'{R}/mouth/crossfade_stats_v4.json','w'),indent=1); [print(k,v) for k,v in stats.items()]
