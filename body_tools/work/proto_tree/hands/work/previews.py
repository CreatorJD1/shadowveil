import numpy as np, json, os, colorsys
from PIL import Image, ImageDraw
from render import *
from defs import D
OUT=f'{ROOT}/hands/previews'; os.makedirs(OUT,exist_ok=True)
FING=['Thumb','Index','Middle','Ring','Pinky']
def colr(pid):
    s,n=pid.split('_')
    if n=='palm': return (170,170,170)
    f=n[:-1]; k=int(n[-1]); h=FING.index(f)/5
    r,g,b=colorsys.hsv_to_rgb(h,[1,.75,.5][k-1],[.85,1,.95][k-1]); return (int(r*255),int(g*255),int(b*255))
def boxes(v):
    bs=[]
    for s,H in D[v].items():
        x0,y0,x1,y1=H['box']; bs.append((s,(x0-25,y0-25,x1+25,y1+25)))
    return sorted(bs,key=lambda t:t[1][0])
def on_white(im):
    bg=Image.new('RGBA',im.size,(255,255,255,255)); bg.alpha_composite(im); return bg.convert('RGB')
def panel(img,box,s=3,title=None):
    c=img.crop(box); c=c.resize((c.size[0]*s,c.size[1]*s),Image.NEAREST)
    if title:
        d=ImageDraw.Draw(c); d.rectangle([0,0,c.size[0],14],fill=(255,255,255)); d.text((3,2),title,fill=(0,0,0))
    return c
def hstack(ims,pad=6,bg=(235,235,235)):
    W_=sum(i.size[0] for i in ims)+pad*(len(ims)+1); H_=max(i.size[1] for i in ims)+2*pad
    o=Image.new('RGB',(W_,H_),bg); x=pad
    for i in ims: o.paste(i,(x,pad)); x+=i.size[0]+pad
    return o
def vstack(ims,pad=6,bg=(235,235,235)):
    W_=max(i.size[0] for i in ims)+2*pad; H_=sum(i.size[1] for i in ims)+pad*(len(ims)+1)
    o=Image.new('RGB',(W_,H_),bg); y=pad
    for i in ims: o.paste(i,(pad,y)); y+=i.size[1]+pad
    return o
POSES={
 'curl_index_middle':lambda s:{f'Hand{s}{f}{k}':1.0 for f in ['Index','Middle'] for k in (1,2,3)},
 'point':lambda s:{**{f'Hand{s}{f}{k}':1.0 for f in ['Middle','Ring','Pinky'] for k in (1,2,3)},f'Hand{s}Thumb2':.8,f'Hand{s}Thumb3':.8,f'Hand{s}ThumbSpread':-0.6},
 'loose_fist':lambda s:{**{f'Hand{s}{f}{k}':0.7 for f in ['Index','Middle','Ring','Pinky'] for k in (1,2,3)},f'Hand{s}Thumb2':.6,f'Hand{s}Thumb3':.6,f'Hand{s}ThumbSpread':-0.4},
 'spread':lambda s:{f'Hand{s}Spread':1.0,f'Hand{s}ThumbSpread':1.0},
}
sheet_rows=[]
for v in ['apose','tpose','left','right','back']:
    base=Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA')
    mask=np.array(Image.open(f'{ROOT}/hands/{v}_hand_erase_mask.png'))>0
    b=np.array(base); be=b.copy(); be[mask]=0
    if v in ('left','right'):
        # MOCK of Base Body's thigh fill behind the hand (preview only)
        from scipy import ndimage as ndi
        ring=ndi.binary_dilation(mask,iterations=6)&~ndi.binary_dilation(mask,iterations=3)
        sk=np.median(b[ring&(b[...,3]==255)][:,:3],0)
        be[mask]=list(sk.astype(np.uint8))+[255]
    bb=Image.fromarray(be,'RGBA')
    rest,rig,_=render(v,bb,skip_hidden=False)
    diff=np.abs(np.array(rest).astype(int)-b.astype(int)).max(2)
    BX=boxes(v)
    # (a) rest
    pa=[]
    for s,bx in BX:
        dimg=Image.fromarray(np.where(diff>0,255,0).astype(np.uint8)).convert('RGBA')
        pa+= [panel(on_white(base),bx,title=f'{s} base.png'),panel(on_white(bb),bx,title='hand erased'+(' (mock thigh)' if v in('left','right') else '')),
              panel(on_white(rest),bx,title='erased + parts @rest'),panel(dimg.convert('RGB'),bx,title=f'diff px={int((diff>0).sum())}')]
    ra=hstack(pa); ra.save(f'{OUT}/{v}_a_rest_match.png')
    # (b) segment map + exploded
    _,imgs=load_rig(v)
    seg=Image.new('RGBA',base.size,(255,255,255,255)); seg.alpha_composite(bb)
    segarr=np.array(seg).astype(float)
    ex=Image.new('RGBA',base.size,(255,255,255,255))
    byid={p['id']:p for p in rig['parts']}
    for p in sorted(rig['parts'],key=lambda p:p['layer']):
        if p['id'] not in imgs or p.get('hidden'): continue
        A=np.array(imgs[p['id']]); vis=A[...,3]>0
        c=np.array(colr(p['id']),float)
        segarr[vis,:3]=0.35*A[vis,:3]+0.65*c
        # exploded: shift by chain depth along direction from palm pivot
        s_,n=p['id'].split('_')
        if n=='palm': off=(0,0)
        else:
            k=int(n[-1]); pal=byid[f'{s_}_palm']
            dv=np.array([p['pivotX']-pal['pivotX'],p['pivotY']-pal['pivotY']]); dv/=np.linalg.norm(dv)+1e-9
            off=tuple((dv*5*k).round().astype(int))
        tint=A.copy().astype(float); tint[vis,:3]=0.5*A[vis,:3]+0.5*c
        ti=Image.fromarray(tint.astype(np.uint8),'RGBA')
        ex.alpha_composite(ti,dest=(int(off[0]),int(off[1])) if off[0]>=0 and off[1]>=0 else (0,0)) if (off[0]>=0 and off[1]>=0) else ex.alpha_composite(ti.transform(ti.size,Image.AFFINE,(1,0,-off[0],0,1,-off[1])))
    segimg=Image.fromarray(segarr.astype(np.uint8),'RGBA')
    d=ImageDraw.Draw(segimg)
    for p in rig['parts']:
        if p['pivotX'] is None or p.get('hidden'): continue
        x,y=p['pivotX'],p['pivotY']; d.ellipse([x-1.5,y-1.5,x+1.5,y+1.5],fill=(255,0,255))
    pb=[]
    for s,bx in BX:
        pb+=[panel(segimg.convert('RGB'),bx,title=f'{s} segments + pivots'),panel(ex.convert('RGB'),bx,title='exploded (5px/joint)')]
    rb=hstack(pb); rb.save(f'{OUT}/{v}_b_segments.png')
    # (c) poses
    pc=[]; posed={}
    for pn,fn in POSES.items():
        prm={}
        for s in D[v]: prm.update(fn(s))
        im,_,_=render(v,bb,prm,skip_hidden=False); posed[pn]=im
        # palm untouched check
        for s,bx in BX: pc.append(panel(on_white(im),bx,title=f'{s} {pn}'))
    rc=hstack(pc); rc.save(f'{OUT}/{v}_c_curl_test.png')
    # full-body curl view (downscaled)
    posed['curl_index_middle'].resize((683,870)); on_white(posed['curl_index_middle']).resize((683,870)).save(f'{OUT}/{v}_c_curl_fullbody.png')
    # contact row
    s0,bx=BX[0]
    row=[panel(on_white(base),bx,2,f'{v} {s0} original'),panel(segimg.convert('RGB'),bx,2,'segments'),panel(on_white(rest),bx,2,f'rest diff={int((diff>0).sum())}')]+\
        [panel(on_white(posed[k]),bx,2,k) for k in POSES]
    if len(BX)>1:
        s1,bx1=BX[1]
        row+=[panel(segimg.convert('RGB'),bx1,2,f'{s1} segments'),panel(on_white(posed['curl_index_middle']),bx1,2,f'{s1} curl'),panel(on_white(posed['loose_fist']),bx1,2,f'{s1} fist')]
    sheet_rows.append(hstack(row))
    print(v,'done',int((diff>0).sum()))
vstack(sheet_rows).save(f'{ROOT}/hands/contact_sheet.png')
print('sheet')
