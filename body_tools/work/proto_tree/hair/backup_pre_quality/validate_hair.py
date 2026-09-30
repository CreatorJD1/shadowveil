#!/usr/bin/env python3
"""Base Hair validation (contract v1.1).
(1) rest: hair_back -> base_body(sim: base.png with hair erase mask alpha=0) -> hair parts; must equal base.png
    except despilled fringe pixels. Also reports the plain 'parts over base.png inside hair mask' comparison.
(2) sway: each swaying part rotated about its pivot by swayWeight*maxSwayDeg*s must not touch the union alpha
    of all eye parts (white/iris/lid_0..4/lash) and all mouth shapes, dilated 2px. s in {-1,-.5,.5,1} plus a fine
    sweep of 41 values in [-1,1]. On overlap maxSwayDeg is lowered in 0.1deg steps until it passes (--fix writes rig.json).
(3) every PNG in hair/ is listed in rig.json, every listed file exists; keyed RGBA, no chroma blue (b>r+40&b>g+40), no white bg.
"""
import json, os, sys, glob, numpy as np
from PIL import Image
from scipy import ndimage as ndi
R='/workspace/shadowveil'; VIEWS=['apose','tpose','left','right','back']
FIX='--fix' in sys.argv
def rgba(p): return np.array(Image.open(p).convert('RGBA')).astype(np.float64)
def over(dst,src):
    sa=src[...,3:]/255; da=dst[...,3:]/255; oa=sa+da*(1-sa)
    oc=np.where(oa>0,(src[...,:3]*sa+dst[...,:3]*da*(1-sa))/np.maximum(oa,1e-9),0)
    return np.concatenate([oc,oa*255],-1)
def q(x): return np.clip(np.round(x),0,255).astype(np.uint8)
def rotmask(m,px,py,deg):
    """Pixels that get any alpha when the part is drawn rotated by deg about (px,py) with bilinear sampling
    (canvas rotate(+deg) turns clockwise on screen, y down)."""
    if deg==0 or not m.any(): return m.copy()
    ys,xs=np.where(m); H,W=m.shape
    t=np.deg2rad(deg); c,s=np.cos(t),np.sin(t)
    # bbox of forward-mapped pixels (+2px margin)
    X=xs-px; Y=ys-py; fx=px+c*X-s*Y; fy=py+s*X+c*Y
    x0=max(0,int(fx.min())-2); x1=min(W,int(fx.max())+3); y0=max(0,int(fy.min())-2); y1=min(H,int(fy.max())+3)
    oy,ox=np.mgrid[y0:y1,x0:x1].astype(float)
    # inverse map output centres to source
    X=ox-px; Y=oy-py; sx=px+c*X+s*Y; sy=py-s*X+c*Y
    src=ndi.map_coordinates(m.astype(float),[sy,sx],order=1,mode='constant',cval=0)
    out=np.zeros_like(m); out[y0:y1,x0:x1]=src>1e-4
    return out
report={}; ok_all=True
for v in VIEWS:
    hd=f'{R}/views/{v}/hair'; RIG=json.load(open(f'{hd}/rig.json')); rig=RIG if isinstance(RIG,list) else RIG['parts']; rep=report[v]={}
    base=rgba(f'{R}/views/{v}/base.png'); H,W=base.shape[:2]
    # (3) files
    listed={e['file'] for e in rig}; onDisk={os.path.basename(p) for p in glob.glob(f'{hd}/*.png')}
    rep['files_unlisted']=sorted(onDisk-listed); rep['files_missing']=sorted(listed-onDisk)
    parts={}; bad=[]
    for e in rig:
        p=rgba(f"{hd}/{e['file']}"); parts[e['id']]=p
        r,g,b,a=[p[...,i] for i in range(4)]
        if p.shape!=(H,W,4): bad.append((e['file'],'size'))
        if ((a>0)&(b>r+40)&(b>g+40)).sum(): bad.append((e['file'],'chroma'))
        if ((a>0)&(r>240)&(g>240)&(b>240)).sum()>50: bad.append((e['file'],'white'))
        if (a==255).all(): bad.append((e['file'],'no alpha'))
        if e['x']!=0 or e['y']!=0: bad.append((e['file'],'offset'))
    rep['file_problems']=bad
    # (1) rest
    em=np.array(Image.open(f'{R}/hair/{v}_hair_erase_mask.png'))>127
    bb=base.copy(); bb[em]=0
    order=sorted(rig,key=lambda e:e['layer'])
    canvas=np.zeros_like(base)
    for e in order:
        if e['layer']<200: canvas=over(canvas,parts[e['id']])
    canvas=over(canvas,bb)
    for e in order:
        if e['layer']>=200: canvas=over(canvas,parts[e['id']])
    out=q(canvas).astype(int); bq=base.astype(int)
    def neq(A,B): return ((A!=B).any(-1))&~((A[...,3]==0)&(B[...,3]==0))  # fully transparent == transparent
    diff=neq(out,bq)
    hairm=np.zeros((H,W),bool)
    for e in rig:
        if e['id']!='hair_back': hairm|=parts[e['id']][...,3]>0
    des=np.zeros((H,W),bool)
    for e in rig:
        p=parts[e['id']]; des|=(p[...,3]>0)&(p[...,:3]!=base[...,:3]).any(-1)&(e['id']!='hair_back')
    bbp=f'{R}/views/{v}/base_body.png'
    if os.path.exists(bbp):
        c2=np.zeros_like(base)
        for e in order:
            if e['layer']<200: c2=over(c2,parts[e['id']])
        c2=over(c2,rgba(bbp))
        for e in order:
            if e['layer']>=200: c2=over(c2,parts[e['id']])
        hmp=f'{R}/hands/{v}_hand_erase_mask.png'
        hm_=np.array(Image.open(hmp)) if os.path.exists(hmp) else np.zeros((H,W),np.uint8)
        hm_=(hm_[...,-1] if hm_.ndim==3 else hm_)>127
        d3=neq(q(c2).astype(int),bq)&~hm_   # hands are not drawn here; hand-mask area excluded
        rep['rest_vs_BODY_base_body_diff_px']=int(d3.sum()); rep['rest_vs_BODY_diff_outside_despill']=int((d3&~des).sum())
        bbm=rgba(bbp); chg=neq(bbm.astype(int),bq)
        swc=np.any([parts[e['id']][...,3]>0 for e in rig if e['swayWeight']>0],0)
        rep['BODY_changed_px']=int(chg.sum()); rep['BODY_changed_px_outside_our_erase_mask']=int((chg&~em).sum())
        rep['our_erase_px_BODY_did_not_clear']=int((em&~chg).sum())
    rep['rest_stack_diff_px']=int(diff.sum()); rep['rest_stack_diff_outside_despill']=int((diff&~des).sum())
    rep['despilled_px']=int(des.sum())
    # plain over-base test inside hair mask
    pb=base.copy()
    for e in order:
        if e['id']!='hair_back': pb=over(pb,parts[e['id']])
    d2=neq(q(pb).astype(int),bq)&hairm
    rep['over_base_diff_in_hairmask']=int(d2.sum()); rep['over_base_diff_outside_despill']=int((d2&~des).sum())
    swa=[parts[e['id']][...,3]>0 for e in rig if e['swayWeight']>0]
    cnt=np.sum(swa,0); uni=cnt>0
    rep['sway_parts_overlap_px']=int((cnt>1).sum())
    rep['erase_mask_vs_sway_union_mismatch_px']=int((uni^em).sum())
    rep['part_px_differing_from_base']=int(sum(((parts[e['id']][...,3]>0)&neq(parts[e['id']].astype(int),bq)).sum() for e in rig if e['id']!='hair_back'))
    # hair_back only where the layer above at rest is fully opaque
    above=np.where(em,np.max([parts[e['id']][...,3] for e in rig if e['swayWeight']>0],0),bb[...,3])
    rep['hair_back_under_soft_px']=int(((parts['hair_back'][...,3]>0)&(above<255)).sum())
    rep['hair_front_soft_px']=int(((parts['hair_front'][...,3]>0)&(parts['hair_front'][...,3]<255)).sum())
    rep['erase_mask_uncovered']=int((em&~np.any([parts[e['id']][...,3]>0 for e in rig if e['swayWeight']>0],0)).sum())
    # (2) sway
    forb=np.zeros((H,W),bool); srcs=[]
    for sub,pat in (('eyes','Eye*_*.png'),('mouth','*.png')):
        for f in glob.glob(f'{R}/views/{v}/{sub}/{pat}'):
            if 'chroma' in f: continue
            forb|=np.array(Image.open(f).convert('RGBA'))[...,3]>0; srcs.append(os.path.basename(f))
    forb=ndi.binary_dilation(forb,iterations=2); rep['forbidden_px']=int(forb.sum()); rep['forbidden_sources']=len(srcs)
    rest_hits={e['id']:int(((parts[e['id']][...,3]>0)&forb).sum()) for e in rig}
    rep['rest_overlap']={k:x for k,x in rest_hits.items() if x}
    S=sorted(set([-1,-.5,.5,1]+list(np.round(np.linspace(-1,1,41),3))))
    clamps=[]; sway={}
    for e in rig:
        if e['swayWeight']<=0: continue
        m=parts[e['id']][...,3]>0; deg=e['maxSwayDeg']; orig=deg
        while True:
            hits={s:int((rotmask(m,e['pivotX'],e['pivotY'],e['swayWeight']*deg*s)&forb).sum()) for s in S}
            if sum(hits.values())==0 or deg<=0: break
            deg=round(deg-0.1,2)
        if deg!=orig:
            clamps.append(dict(id=e['id'],from_deg=orig,to_deg=deg)); e['maxSwayDeg']=deg
        sway[e['id']]=dict(maxSwayDeg=deg,overlap_px_at_final=sum(hits.values()))
    rep['sway']=sway; rep['clamps']=clamps
    if clamps and FIX: json.dump(RIG,open(f'{hd}/rig.json','w'),indent=1)
    ok=(not rep['files_unlisted'] and not rep['files_missing'] and not bad and rep['rest_stack_diff_outside_despill']==0
        and not rep['rest_overlap'] and all(x['overlap_px_at_final']==0 for x in sway.values()) and rep['erase_mask_uncovered']==0 and rep['sway_parts_overlap_px']==0 and rep['erase_mask_vs_sway_union_mismatch_px']==0 and rep['part_px_differing_from_base']==0 and rep['hair_back_under_soft_px']==0
        and (not clamps or FIX))
    rep['PASS']=bool(ok); ok_all&=ok
    print(v,json.dumps({k:x for k,x in rep.items() if k!='sway'}),flush=True)
json.dump(report,open(f'{R}/hair/validation.json','w'),indent=1)
print('ALL PASS' if ok_all else 'FAIL')
