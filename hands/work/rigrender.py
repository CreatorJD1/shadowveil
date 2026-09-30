"""Python port of rig/index.html hand math: angle = v['Hand'+H+Finger] * maxCurlDeg for every joint of that finger,
+ Spread on finger 1, + ThumbSpread on Thumb1; M = parent * rotAt(pivot, angle); drawn by layer, all parts with a file."""
import json, numpy as np, re
from PIL import Image, ImageDraw
ROOT='/workspace/shadowveil'; W,Hh=1365,1739
PRESETS={'Open':[0,0,0,0,0],'Fist':[1,1,1,1,1],'Point':[1,0,1,1,1],'Peace':[1,0,0,1,1]}
FING=['Thumb','Index','Middle','Ring','Pinky']
def rotAt(px,py,deg):
    t=np.deg2rad(deg); c,s=np.cos(t),np.sin(t)
    return np.array([[c,-s,px-c*px+s*py],[s,c,py-s*px-c*py],[0,0,1]])
def preset(name):
    v={}
    for h in 'LR':
        for f,x in zip(FING,PRESETS[name]): v[f'Hand{h}{f}']=x
    return v
def hand_angle(rig,v,p):
    m=re.match(r'^([LR])_(Thumb|Index|Middle|Ring|Pinky)(\d)$',p['id'])
    if not m: return 0.0
    h,f,n=m.groups(); a=v.get(f'Hand{h}{f}',0)*(p.get('maxCurlDeg') or 0)
    sp=rig.get('spread',{})
    if n=='1':
        S=sp.get(f'Hand{h}Spread')
        if S and f in S.get('fingers',{}): a+=v.get(f'Hand{h}Spread',0)*S['fingers'][f]['maxSpreadDeg']
        T=sp.get(f'Hand{h}ThumbSpread')
        if f=='Thumb' and T:
            x=v.get(f'Hand{h}ThumbSpread',0); a+= x*T['degAtPlus1'] if x>=0 else abs(x)*T['degAtMinus1']
    return a
def chain(rig,v):
    by={p['id']:p for p in rig['parts']}; M={}
    def m(i):
        if i in M: return M[i]
        p=by[i]; par=m(p['parent']) if p.get('parent') in by else np.eye(3)
        M[i]=par@rotAt(p.get('pivotX') or 0,p.get('pivotY') or 0,hand_angle(rig,v,p)); return M[i]
    for i in by: m(i)
    return M
_cache={}
def img(path):
    if path not in _cache: _cache[path]=Image.open(path).convert('RGBA')
    return _cache[path]
def render(view,v,handsdir=None,base='base_body.png',framesdir=None):
    handsdir=handsdir or f'{ROOT}/views/{view}/hands'
    rig=json.load(open(f'{handsdir}/rig.json'))
    out=img(f'{ROOT}/views/{view}/{base}').copy(); M=chain(rig,v)
    for p in sorted(rig['parts'],key=lambda p:p['layer']):
        if not p.get('file'): continue
        fn=f"{handsdir}/{p['file']}"
        mm=re.match(r'^([LR])_(Thumb|Index|Middle|Ring|Pinky)(\d)$',p['id'])
        fr=p.get('frames')
        if (framesdir or fr) and mm:
            fi=int(round(v.get(f'Hand{mm.group(1)}{mm.group(2)}',0)*2))
            fn=f"{framesdir}/{p['id']}_f{fi}.png" if framesdir else f"{handsdir}/{fr[fi]}"
        im=Image.open(fn).convert('RGBA'); m=M[p['id']]
        if np.allclose(m,np.eye(3)): out.alpha_composite(im); continue
        inv=np.linalg.inv(m)
        out.alpha_composite(im.convert('RGBa').transform((W,Hh),Image.AFFINE,tuple(inv[0])+tuple(inv[1]),resample=Image.BILINEAR).convert('RGBA'))
    return out,rig
def hand_boxes(rig):
    bs=[]
    for h,d in rig['hands'].items():
        if d.get('visible'): b=d['box']; bs.append((h,(b[0]-30,b[1]-30,b[2]+30,b[3]+30)))
    return sorted(bs,key=lambda t:t[1][0])
def sheet(view,handsdir=None,out=None,s=3,title=''):
    rows=[]
    for pn in ['Open','Fist','Point','Peace']:
        im,rig=render(view,preset(pn),handsdir)
        bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); bg=bg.convert('RGB')
        cells=[]
        for h,b in hand_boxes(rig):
            c=bg.crop(b); c=c.resize((c.size[0]*s,c.size[1]*s),Image.NEAREST)
            d=ImageDraw.Draw(c); d.rectangle([0,0,c.size[0],14],fill='white'); d.text((3,2),f'{title} {view} {h} {pn}',fill='black'); cells.append(c)
        rows.append(cells)
    Wc=sum(c.size[0] for c in rows[0])+6*(len(rows[0])+1); Hc=max(c.size[1] for c in rows[0])
    o=Image.new('RGB',(Wc,len(rows)*(Hc+6)+6),(220,220,220))
    for r,cells in enumerate(rows):
        x=6
        for c in cells: o.paste(c,(x,6+r*(Hc+6))); x+=c.size[0]+6
    if out: o.save(out)
    return o
