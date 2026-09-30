#!/usr/bin/env python3
"""Base Hair validation (contract v1.3, parent-chained sway with independent per-segment drives).
(1) rest: hair_back -> base_body(sim: base.png with hair erase mask alpha=0) -> hair parts; must equal base.png
    except despilled fringe pixels. Also reports the plain 'parts over base.png inside hair mask' comparison.
(2) sway: every part is drawn with its world matrix exactly as rig/index.html chains it: M(p)=M(parent)*rotAt(pivot,
    swayWeight*maxSwayDeg*HairSwayX), then translated by dy=round(HairSwayY*swayY*swayYMaxPx) (not inherited).
    Its drawn alpha must not touch the union alpha of all eye parts (white/iris/lid_0..4/lash) and all mouth shapes,
    dilated 2px. v1.3: each segment's drive is independent, so the sweep is a grid: own s over 45 values in [-1,1] x every
    swaying ancestor's s over 21 values x every reachable own dy (HairSwayY/drive in [-1,1]); exact bilinear coverage.
    On overlap the hitting segment's own maxSwayDeg is lowered first (0.1deg steps), then its ancestors', and the
    segment is raised back as far as it stays clean (--fix writes rig.json).
(4) joint caps: a pixel may sit in two parts only as a hidden joint cap: child pixel, drawn under its parent (lower
    layer), both fully opaque and both exact base.png copies, so at rest it is covered by an identical pixel.
(5) rig.json: v1.2 object, required fields, parents exist, no cycles, layers integer and in the hair bands.
(6) wisp exemption: pixels in hair/<view>_eye_crossing_wisp_mask.png that belong to a static (swayWeight 0) part
    are a drawn wisp crossing the eye, cut out of the eye parts by Base Eyes. They are excluded from the rule
    'erase mask == union of swaying parts' (and erase_mask_uncovered) and from the eye/mouth margin at rest.
(3) every PNG in hair/ is listed in rig.json, every listed file exists; keyed RGBA, no chroma blue (b>r+40&b>g+40), no white bg.
"""
import json, os, sys, glob, numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0,'/workspace/shadowveil/hair/tools'); import sway_grid as SG
R='/workspace/shadowveil'; VIEWS=['apose','tpose','left','right','back']
FIX='--fix' in sys.argv
def rgba(p): return np.array(Image.open(p).convert('RGBA')).astype(np.float64)
def over(dst,src):
    sa=src[...,3:]/255; da=dst[...,3:]/255; oa=sa+da*(1-sa)
    oc=np.where(oa>0,(src[...,:3]*sa+dst[...,:3]*da*(1-sa))/np.maximum(oa,1e-9),0)
    return np.concatenate([oc,oa*255],-1)
def q(x): return np.clip(np.round(x),0,255).astype(np.uint8)
def mul(a,b): return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]]
def rotAt(px,py,deg):
    t=np.deg2rad(deg); c,s=np.cos(t),np.sin(t); return [c,s,-s,c,px-c*px+s*py,py-s*px-c*py]
IDM=[1,0,0,1,0,0]
def chain(rig,sx):
    """rotation-only world matrices, same recursion as rig/index.html chain()"""
    by={e['id']:e for e in rig}; M={}
    def m(i):
        if i in M: return M[i]
        e=by[i]; q=e.get('parent'); b=m(q) if q and q in by else IDM
        M[i]=mul(b,rotAt(e.get('pivotX',0),e.get('pivotY',0),(e.get('swayWeight') or 0)*(e.get('maxSwayDeg') or 0)*sx)); return M[i]
    for e in rig: m(e['id'])
    return M
def jsround(x): return int(np.floor(x+0.5))
_bb={}
def affmask(m,M):
    """Pixels that get any alpha when the full-canvas mask is drawn with canvas transform M (bilinear sampling;
    canvas rotate(+deg) turns clockwise on screen, y down)."""
    if np.allclose(M,IDM) or not m.any(): return m.copy(),(0,0)
    k=id(m)
    if k not in _bb:
        ys,xs=np.where(m); sy0,sy1,sx0,sx1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
        _bb[k]=(m,xs,ys,sy0,sx0,np.pad(m[sy0:sy1,sx0:sx1].astype(float),1))
    _,xs,ys,sy0,sx0,crop=_bb[k]; H,W=m.shape; a,b,c,d,e,f=M
    fx=a*(xs+.5)+c*(ys+.5)+e; fy=b*(xs+.5)+d*(ys+.5)+f
    x0=max(0,int(fx.min())-3); x1=min(W,int(fx.max())+4); y0=max(0,int(fy.min())-3); y1=min(H,int(fy.max())+4)
    oy,ox=np.mgrid[y0:y1,x0:x1].astype(float); det=a*d-b*c
    X=ox+.5-e; Y=oy+.5-f; sx=(d*X-c*Y)/det-.5; sy=(-b*X+a*Y)/det-.5
    src=ndi.map_coordinates(crop,[sy-sy0+1,sx-sx0+1],order=1,mode='constant',cval=0)
    out=np.zeros_like(m); out[y0:y1,x0:x1]=src>1e-4
    return out,(y0,y1)
def shifted(m,dy):
    if dy==0: return m
    o=np.zeros_like(m)
    if dy>0: o[dy:]=m[:-dy]
    else: o[:dy]=m[-dy:]
    return o
report={}; ok_all=True
for v in VIEWS:
    hd=f'{R}/views/{v}/hair'; RIG=json.load(open(f'{hd}/rig.json')); rig=RIG if isinstance(RIG,list) else RIG['parts']; rep=report[v]={}
    base=rgba(f'{R}/views/{v}/base.png'); H,W=base.shape[:2]
    # (3) files
    listed={e['file'] for e in rig}; onDisk={os.path.basename(p) for p in glob.glob(f'{hd}/*.png')}
    rep['files_unlisted']=sorted(onDisk-listed); rep['files_missing']=sorted(listed-onDisk)
    parts={}; bad=[]; em0=np.array(Image.open(f'{R}/hair/{v}_hair_erase_mask.png'))>127
    for e in rig:
        p=rgba(f"{hd}/{e['file']}"); parts[e['id']]=p
        r,g,b,a=[p[...,i] for i in range(4)]
        if p.shape!=(H,W,4): bad.append((e['file'],'size'))
        # speck fix: in a swaying strand, a px that is an exact base.png copy (RGBA) inside the hair erase mask is her navy hair
        if ((a>0)&(b>r+40)&(b>g+40)&~((p==base).all(-1)&em0&(e['swayWeight']>0))).sum(): bad.append((e['file'],'chroma'))
        if ((a>0)&(r>240)&(g>240)&(b>240)).sum()>50: bad.append((e['file'],'white'))
        if (a==255).all(): bad.append((e['file'],'no alpha'))
        if e['x']!=0 or e['y']!=0: bad.append((e['file'],'offset'))
    rep['file_problems']=bad
    rp=[]
    if not isinstance(RIG,dict) or not isinstance(RIG.get('parts'),list): rp.append('not a v1.2 object')
    if not isinstance(RIG,dict) or not isinstance(RIG.get('swayYMaxPx'),(int,float)): rp.append('swayYMaxPx missing')
    ids=[e['id'] for e in rig]; byid={e['id']:e for e in rig}
    if len(set(ids))!=len(ids): rp.append('duplicate ids')
    for e in rig:
        for k in ('id','file','x','y','pivotX','pivotY','parent','layer','swayWeight','maxSwayDeg','swayY'):
            if k not in e: rp.append(e['id']+': missing '+k)
        if e.get('parent') is not None and e['parent'] not in byid: rp.append(e['id']+': unknown parent '+str(e['parent']))
        if not (isinstance(e.get('layer'),int) and (100<=e['layer']<=199 or 600<=e['layer']<=699)): rp.append(e['id']+': layer out of hair bands')
        if not (0<=e.get('swayWeight',0)<=1 and 0<=e.get('swayY',0)<=1 and e.get('maxSwayDeg',0)>=0): rp.append(e['id']+': weight/swayY/deg range')
        seen=set(); cur=e['id']
        while cur is not None and cur in byid:
            if cur in seen: rp.append(e['id']+': parent cycle'); break
            seen.add(cur); cur=byid[cur].get('parent')
    rep['rig_problems']=rp
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
    # joint caps: child pixel that is also in its parent, parent drawn above (higher layer), both opaque base copies
    capm=np.zeros((H,W),bool); ok_shared=np.zeros((H,W),int)
    for e in rig:
        p=e.get('parent'); 
        if e['swayWeight']<=0 or p not in byid or byid[p]['swayWeight']<=0: continue
        A=parts[e['id']][...,3]; B=parts[p][...,3]
        both=(A>0)&(B>0)
        good=both&(A==255)&(B==255)&(byid[p]['layer']>e['layer'])
        capm|=good; ok_shared+=good
    rep['joint_cap_px']=int(capm.sum())
    rep['sway_parts_overlap_px']=int(((cnt-ok_shared)>1).sum())  # shared pixels that are not hidden joint caps
    # (6) static eye-crossing wisp exemption (only pixels owned by a non-swaying part)
    wp=f'{R}/hair/{v}_eye_crossing_wisp_mask.png'
    wx=(np.array(Image.open(wp).convert('L'))>127) if os.path.exists(wp) else np.zeros((H,W),bool)
    wx&=np.any([parts[e['id']][...,3]>0 for e in rig if e['swayWeight']<=0],0)&~uni
    rep['wisp_exempt_px']=int(wx.sum())
    rep['erase_mask_vs_sway_union_mismatch_px']=int(((uni^em)&~wx).sum())
    rep['part_px_differing_from_base']=int(sum(((parts[e['id']][...,3]>0)&neq(parts[e['id']].astype(int),bq)).sum() for e in rig if e['id']!='hair_back'))
    # hair_back only where the layer above at rest is fully opaque
    above=np.where(em,np.max([parts[e['id']][...,3] for e in rig if e['swayWeight']>0],0),bb[...,3])
    # 2026-09-30 (wisp underfill): static hair parts drawn above hair_back (layer>=200, e.g. hair_front over the exempt
    # tpose wisp) also hide hair_back at rest, so their alpha counts as 'above' too.
    above=np.maximum(above,np.max([parts[e['id']][...,3] for e in rig if e['swayWeight']<=0 and e['layer']>=200]+[np.zeros((H,W))],0))
    rep['hair_back_under_soft_px']=int(((parts['hair_back'][...,3]>0)&(above<255)).sum())
    rep['hair_front_soft_px']=int(((parts['hair_front'][...,3]>0)&(parts['hair_front'][...,3]<255)).sum())
    rep['erase_mask_uncovered']=int((em&~np.any([parts[e['id']][...,3]>0 for e in rig if e['swayWeight']>0],0)&~wx).sum())
    # (2) sway
    forb=np.zeros((H,W),bool); srcs=[]
    for sub,pat in (('eyes','Eye*_*.png'),('mouth','*.png')):
        for f in glob.glob(f'{R}/views/{v}/{sub}/{pat}'):
            if 'chroma' in f: continue
            forb|=np.array(Image.open(f).convert('RGBA'))[...,3]>0; srcs.append(os.path.basename(f))
    forb=ndi.binary_dilation(forb,iterations=2); rep['forbidden_px']=int(forb.sum()); rep['forbidden_sources']=len(srcs)
    rest_hits={e['id']:int(((parts[e['id']][...,3]>0)&forb&~(wx if e['swayWeight']<=0 else False)).sum()) for e in rig}
    # 2026-09-30 (wisp underfill): a static (swayWeight 0) part drawn below the eye band (layer<400) can never cover a face part:
    # it is drawn under the eyes/mouth and never moves relative to them. Its pixels next to/under the face are reported as
    # under_face_static_px (informational) instead of rest_overlap; hair_back_under_soft_px already proves they are hidden at rest.
    under={e['id'] for e in rig if e['swayWeight']<=0 and e['layer']<400}
    rep['under_face_static_px']={k:x for k,x in rest_hits.items() if x and k in under}
    rest_hits={k:(0 if k in under else x) for k,x in rest_hits.items()}
    rep['rest_overlap']={k:x for k,x in rest_hits.items() if x}
    # v1.3: every segment's drive s is independent -> grid: own s (45 values) x each swaying ancestor's s (21 values)
    # x the part's own vertical drive (every reachable dy). Exact bilinear coverage, see hair/tools/sway_grid.py.
    ymax=RIG.get('swayYMaxPx',0) if isinstance(RIG,dict) else 0
    masks={e['id']:parts[e['id']][...,3]>0 for e in rig}
    def anc(e):
        out=[]; cur=byid.get(e.get('parent')) if e.get('parent') else None
        while cur is not None:
            if cur['swayWeight']>0: out.append(cur)
            cur=byid.get(cur.get('parent')) if cur.get('parent') else None
        return out[::-1]                                   # root first
    def H_(e): return SG.hits(e,anc(e),masks[e['id']],forb,ymax)
    def bisect_max(c,test,hi):
        """largest deg in [0,hi] (0.1 steps) with test()==True, assuming monotone; None if even 0 fails"""
        c['maxSwayDeg']=0.0
        if not test(): return None
        lo_,hi_=0,int(round(hi*10))
        c['maxSwayDeg']=hi_/10
        if test(): return hi_/10
        while hi_-lo_>1:
            mid=(lo_+hi_)//2; c['maxSwayDeg']=mid/10
            if test(): lo_=mid
            else: hi_=mid
        c['maxSwayDeg']=lo_/10; return lo_/10
    orig={e['id']:e['maxSwayDeg'] for e in rig}
    sw_parts=sorted([e for e in rig if e['swayWeight']>0],key=lambda e:len(anc(e)))
    for it in range(3):
        changed=False
        for e in sw_parts:
            if rest_hits.get(e['id']): continue   # touches a face part at rest: no sway clamp can fix it (reported)
            if H_(e)==0: continue
            changed=True; members=[e]+anc(e)[::-1]    # own segment first, then parent, grandparent...
            for i,c in enumerate(members):
                got=bisect_max(c,lambda:H_(e)==0,c['maxSwayDeg'])
                if got is not None:
                    for lower in members[:i][::-1]:      # an ancestor gave way: raise the lower segments back up
                        desc=[x for x in sw_parts if lower in anc(x) or x is lower]
                        bisect_max(lower,lambda:all(H_(x)==0 for x in desc),orig[lower['id']])
                    break
                c['maxSwayDeg']=0.0
        if not changed: break
    clamps=[dict(id=e['id'],from_deg=orig[e['id']],to_deg=e['maxSwayDeg']) for e in rig if e['maxSwayDeg']!=orig[e['id']]]
    sway={e['id']:dict(maxSwayDeg=e['maxSwayDeg'],rotDegAtS1=round(e['swayWeight']*e['maxSwayDeg'],3),ancestors=[x['id'] for x in anc(e)],overlap_px_at_final=H_(e)) for e in sw_parts}
    rep['sweep']='v1.3 independent drives: own s x %d, each ancestor s x %d, own dy in all reachable values'%(len(SG.S_OWN),len(SG.S_ANC))
    rep['sway']=sway; rep['clamps']=clamps
    if clamps and FIX: json.dump(RIG,open(f'{hd}/rig.json','w'),indent=1)
    ok=(not rep['rig_problems'] and not rep['files_unlisted'] and not rep['files_missing'] and not bad and rep['rest_stack_diff_outside_despill']==0
        and not rep['rest_overlap'] and all(x['overlap_px_at_final']==0 for x in sway.values()) and rep['erase_mask_uncovered']==0 and rep['sway_parts_overlap_px']==0 and rep['erase_mask_vs_sway_union_mismatch_px']==0 and rep['part_px_differing_from_base']==0 and rep['hair_back_under_soft_px']==0
        and (not clamps or FIX))
    rep['PASS']=bool(ok); ok_all&=ok
    print(v,json.dumps({k:x for k,x in rep.items() if k!='sway'}),flush=True)
json.dump(report,open(f'{R}/hair/validation.json','w'),indent=1)
print('ALL PASS' if ok_all else 'FAIL')
