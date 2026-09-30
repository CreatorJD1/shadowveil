import sys, json, itertools, numpy as np
sys.path.insert(0,'/workspace/shadowveil/eyes/tools')
from render_eyes import render, DEFAULT_BASE
from PIL import Image, ImageDraw
OUT='/workspace/shadowveil/eyes'
VIEWS={'apose':['EyeR','EyeL'],'tpose':['EyeR','EyeL'],'left':['EyeL'],'right':['EyeR']}
res={}
def zoomcrop(img,box,s=6):
    im=Image.fromarray(img,'RGBA'); bg=Image.new('RGBA',im.size,(40,40,40,255)); bg.alpha_composite(im)
    c=bg.crop(box).convert('RGB'); return c.resize((c.width*s,c.height*s),Image.NEAREST)
for v,eyes in VIEWS.items():
    BASE=f'/workspace/shadowveil/views/{v}/base.png'; base=np.array(Image.open(BASE).convert('RGBA'))
    masks=[np.load(f'{v}_{e}_mask.npy') for e in eyes]; allm=np.zeros(base.shape[:2],bool)
    for m in masks: allm|=m
    rest=render(v)
    d=np.abs(rest.astype(int)-base.astype(int))
    import os
    BB=f'/workspace/shadowveil/views/{v}/base_body.png'
    if os.path.exists(BB):
        bbimg=np.array(Image.open(BB).convert('RGBA')).astype(int)
        restbb=render(v,base=BB).astype(int)
        import glob as _g
        cov=np.zeros(base.shape[:2],bool)
        for f in _g.glob(f'/workspace/shadowveil/views/{v}/eyes/*.png'):
            if not f.endswith('_chroma.png'): cov|=np.array(Image.open(f))[...,3]>0
        diffbb=np.abs(bbimg-base.astype(int)).max(2)>0
        dd=np.abs(restbb-base.astype(int)).max(2)>0
        bb_stats=dict(base_body_vs_base_px=int(diffbb.sum()),base_body_vs_base_px_inside_eye_parts=int((diffbb&cov).sum()),
                      rest_over_base_body_vs_base_inside_eye_parts_px=int((dd&cov).sum()),
                      rest_over_base_body_vs_base_inside_eye_regions_px=int((dd&allm).sum()),
                      rest_over_base_body_max_in_eye_regions=int(np.abs(restbb-base.astype(int))[allm].max()))
    else: bb_stats='no base_body.png'
    # eye region = opening bbox padded 6px
    ys,xs=np.nonzero(allm); ey=slice(ys.min()-6,ys.max()+7); ex=slice(xs.min()-6,xs.max()+7)
    r=dict(base_body_check=bb_stats,rest_max_full=int(d.max()),rest_mean_full=float(d.mean()),rest_max_eye=int(d[ey,ex].max()),rest_mean_eye=float(d[ey,ex].mean()),rest_changed_px=int((d.max(2)>0).sum()))
    # diff image: eye crop of base | rest | |diff|*16
    box=(xs.min()-14,ys.min()-12,xs.max()+15,ys.max()+13)
    dimg=np.zeros_like(base); dimg[...,:3]=np.clip(d[...,:3]*16,0,255); dimg[...,3]=255
    tiles=[zoomcrop(base,box),zoomcrop(rest,box),zoomcrop(dimg,box)]
    W=sum(t.width for t in tiles)+20; sheet=Image.new('RGB',(W,tiles[0].height+22),(30,30,30)); x=0
    for t,lab in zip(tiles,['original','rest render','|diff| x16 (black = identical)']):
        sheet.paste(t,(x,22)); ImageDraw.Draw(sheet).text((x+4,4),lab,fill=(255,255,0)); x+=t.width+10
    ImageDraw.Draw(sheet).text((4,sheet.height-14),f"max={r['rest_max_full']} mean={r['rest_mean_full']:.4f} changed_px={r['rest_changed_px']}",fill=(0,255,0))
    sheet.save(f'{OUT}/rest_diff_{v}.png')
    # sweep: outside-eye pixels never change; changed pixels subset of eye openings
    worst_out=0; ncombo=0
    nL=int(json.load(open(f'/workspace/shadowveil/views/{v}/eyes/rig.json')).get('lidFrames',5))
    opens=[(1-k/(nL-1),1-k/(nL-1)) for k in range(nL)]+[(0,1),(1,0),(0.5,1),(1,0.5)]
    for (lo,ro),X,Y in itertools.product(opens,[-1,0,1],[-1,0,1]):
        img=render(v,dict(EyeLOpen=lo,EyeROpen=ro,EyeBallX=X,EyeBallY=Y))
        ch=np.abs(img.astype(int)-base.astype(int)).max(2)>0
        worst_out=max(worst_out,int((ch&~allm).sum())); ncombo+=1
    r['sweep_combos']=ncombo; r['changed_px_outside_eye_openings_max']=worst_out
    # preview sheet
    states=[('rest',{}),('half blink',dict(EyeLOpen=.5,EyeROpen=.5)),('closed',dict(EyeLOpen=0,EyeROpen=0)),
            ('look left (X=-1, her right)',dict(EyeBallX=-1)),('look right (X=+1)',dict(EyeBallX=1)),
            ('look up (Y=-1)',dict(EyeBallY=-1)),('look down (Y=+1)',dict(EyeBallY=1)),('both closed + gaze X=-1',dict(EyeLOpen=0,EyeROpen=0,EyeBallX=-1))]
    if v in ('apose','tpose'): states.insert(3,('wink: EyeR closed',dict(EyeROpen=0)))
    if v in ('apose','tpose'): fbox=(600,180,770,270)
    elif v=='left': fbox=(560,170,680,260)
    else: fbox=(700,170,820,260)
    s=4 if v in ('apose','tpose') else 5
    tiles=[(n,zoomcrop(render(v,pp),fbox,s)) for n,pp in states]
    cols=3; tw,th=tiles[0][1].size; rows=(len(tiles)+cols-1)//cols
    sheet=Image.new('RGB',(cols*(tw+8),rows*(th+24)),(30,30,30))
    for i,(n,t) in enumerate(tiles):
        x=(i%cols)*(tw+8); y=(i//cols)*(th+24); sheet.paste(t,(x,y+20)); ImageDraw.Draw(sheet).text((x+4,y+4),n,fill=(255,255,0))
    sheet.save(f'{OUT}/preview_{v}.png')
    # key checks on delivered parts
    import glob
    bad=[]
    for f in sorted(glob.glob(f'/workspace/shadowveil/views/{v}/eyes/*.png')):
        if f.endswith('_chroma.png'): continue
        a=np.array(Image.open(f)); assert a.shape==(1739,1365,4),f
        al=a[...,3]; op=al>0
        nearblue=op&(np.abs(a[...,:3].astype(int)-[0,0,255]).max(2)<=60)
        import re as _re
        aa_ok=bool(_re.search(r'_lid_[1-9]\.png$',f))
        if nearblue.any() or (not aa_ok and not set(np.unique(al))<= {0,255}): bad.append(f)
        # "white background": no opaque pixels outside eye opening+lash bbox region
    r['parts_checked']=len(glob.glob(f'/workspace/shadowveil/views/{v}/eyes/*[!a].png')); r['bad_parts']=bad
    res[v]=r
    import render_eyes as _re_mod; _re_mod._cache.clear(); import gc; gc.collect()
json.dump(res,open(f'{OUT}/verification.json','w'),indent=1); print(json.dumps(res,indent=1))
