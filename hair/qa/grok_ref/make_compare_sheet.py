from PIL import Image, ImageDraw, ImageFont
import json, numpy as np
S='/workspace/shadowveil'; R=S+'/reference/grok_build/public/clean-room/layers/hair/'
def font(n):
    try: return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
    except: return ImageFont.load_default()
F=font(18); Fs=font(13)
def refcrop(x):
    im=Image.open(R+f'hair-{x}.png').convert('RGB'); a=np.array(im).astype(int)
    m=(a[...,2]-np.maximum(a[...,0],a[...,1]))<40; ys,xs=np.where(m)
    return im.crop((xs.min()-10,ys.min()-10,xs.max()+10,ys.max()+10))
def ourhair(v):
    j=json.load(open(f'{S}/views/{v}/hair/rig.json')); acc=Image.new('RGBA',(1365,1739),(0,0,255,255))
    for p in sorted(j['parts'],key=lambda p:p['layer']): acc.alpha_composite(Image.open(f'{S}/views/{v}/hair/'+p['file']).convert('RGBA'))
    bb=None
    for p in j['parts']:
        b=Image.open(f'{S}/views/{v}/hair/'+p['file']).split()[-1].getbbox()
        if b: bb=b if bb is None else (min(bb[0],b[0]),min(bb[1],b[1]),max(bb[2],b[2]),max(bb[3],b[3]))
    return acc.crop((bb[0]-4,bb[1]-4,bb[2]+4,bb[3]+4)).convert('RGB'),bb,len([p for p in j['parts'] if p['id'].startswith('strand') and not p['id'].endswith('_tip')])
def ourbase(v,bb):
    b=Image.open(f'{S}/views/{v}/base.png').convert('RGBA'); bg=Image.new('RGBA',b.size,(0,0,255,255)); bg.alpha_composite(b)
    return bg.crop((bb[0]-70,bb[1]-5,bb[2]+70,bb[3]+160)).convert('RGB')
def fit(im,w,h):
    s=min(w/im.width,h/im.height); im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
    c=Image.new('RGB',(w,h),(0,0,255)); c.paste(im,((w-im.width)//2,(h-im.height)//2)); return c
angles=['000','045','090','135','180','225','270','315']
match={'000':'apose','090':'left','180':'back','270':'right'}
cw,ch=300,380; pad=8; top=40; lab=26
rows=['Reference hair-XXX.png (new)','Ours: composited hair parts','Ours: views/<v>/base.png']
W=90+len(angles)*(cw+pad); H=top+3*(ch+lab)+140
sheet=Image.new('RGB',(W,H),(24,24,28)); d=ImageDraw.Draw(sheet)
d.text((10,8),'Shadowveil hair: Clean-room reference turnaround (commit a63fd8e, PNGs as of 01:06 PT) vs our drawn views. Same-height fit per cell; not to common scale.',fill=(230,230,230),font=Fs)
colors=json.load(open('/tmp/gr/colors.json'))
for i,a in enumerate(angles):
    x=90+i*(cw+pad); y=top
    d.text((x,y),f'{a}°'+(f'  ↔ {match[a]}' if a in match else '  (no drawn view)'),fill=(255,220,120),font=F)
    sheet.paste(fit(refcrop(a),cw,ch),(x,y+lab))
    if a in match:
        v=match[a]; oh,bb,ns=ourhair(v)
        d.text((x,y+ch+lab+2),f'ours {v}: {ns} strands',fill=(200,230,255),font=Fs)
        sheet.paste(fit(oh,cw,ch),(x,y+ch+2*lab))
        d.text((x,y+2*ch+2*lab+2),f'{v} base drawing',fill=(200,230,255),font=Fs)
        sheet.paste(fit(ourbase(v,bb),cw,ch),(x,y+2*ch+3*lab))
    else:
        d.rectangle((x,y+ch+2*lab,x+cw,y+3*ch+3*lab),outline=(80,80,80))
        d.text((x+10,y+ch+2*lab+10),'no drawn view at this angle',fill=(150,150,150),font=Fs)
    # swatches: kmeans clusters
    sy=top+3*(ch+lab)+10
    for j,(rgb,frac) in enumerate(colors['ref_'+a]['km']):
        d.rectangle((x+j*40,sy,x+j*40+36,sy+26),fill=tuple(rgb)); d.text((x+j*40,sy+28),'%d,%d,%d'%tuple(rgb),fill=(200,200,200),font=font(9))
    d.text((x,sy+42),'ref',fill=(200,200,200),font=Fs)
    if a in match:
        for j,(rgb,frac) in enumerate(colors['our_'+match[a]]['km']):
            d.rectangle((x+j*40,sy+62,x+j*40+36,sy+88),fill=tuple(rgb)); d.text((x+j*40,sy+90),'%d,%d,%d'%tuple(rgb),fill=(200,200,200),font=font(9))
        d.text((x,sy+104),'ours',fill=(200,200,200),font=Fs)
for k,t in enumerate(rows): d.text((6,top+lab+k*(ch+lab)+ch//2),'\n'.join(t.split(': ')),fill=(220,220,220),font=font(11))
sheet.save(S+'/hair/qa/grok_ref/compare_sheet.png'); print(sheet.size)
