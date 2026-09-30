#!/usr/bin/env python3
"""Lift sway clamps that are no longer needed (contract v1.3 sweep, same as validate_hair.py): for every swaying part,
root first, raise maxSwayDeg in 0.1 deg steps toward CAP while the part and every descendant stay clear of the eye/mouth
forbidden area (all eye parts incl. every lid frame + all mouth shapes, dilated 2 px), sweeping own s x 45,
each swaying ancestor's s x 21 and every reachable own dy (HairSwayY in [-1,1]). --write updates rig.json."""
import json, sys, glob, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import sway_grid as SG
R='/workspace/shadowveil'; CAP=float(os.environ.get('CAP',10.0)); WRITE='--write' in sys.argv
views=[a for a in sys.argv[1:] if not a.startswith('--')] or ['apose','tpose','left','right','back']
out={}
for v in views:
    hd=f'{R}/views/{v}/hair'; RIG=json.load(open(f'{hd}/rig.json')); rig=RIG['parts']; by={e['id']:e for e in rig}; ymax=RIG.get('swayYMaxPx',0)
    forb=None
    for sub,pat in (('eyes','Eye*_*.png'),('mouth','*.png')):
        for f in glob.glob(f'{R}/views/{v}/{sub}/{pat}'):
            if 'chroma' in f: continue
            a=np.array(Image.open(f).convert('RGBA'))[...,3]>0; forb=a if forb is None else forb|a
    if forb is None: forb=np.zeros(np.array(Image.open(f'{R}/views/{v}/base.png')).shape[:2],bool)  # back view: no face parts
    forb=ndi.binary_dilation(forb,iterations=2)
    masks={e['id']:np.array(Image.open(f"{hd}/{e['file']}").convert('RGBA'))[...,3]>0 for e in rig}
    def anc(e):
        o=[]; c=by.get(e.get('parent'))
        while c is not None:
            if c['swayWeight']>0: o.append(c)
            c=by.get(c.get('parent'))
        return o[::-1]
    H_=lambda e: SG.hits(e,anc(e),masks[e['id']],forb,ymax)
    sw=sorted([e for e in rig if e['swayWeight']>0],key=lambda e:len(anc(e)))
    before={e['id']:e['maxSwayDeg'] for e in sw}; log={}
    for c in sw:
        desc=[x for x in sw if x is c or c in anc(x)]
        ok=lambda: all(H_(x)==0 for x in desc)
        cur=c['maxSwayDeg']
        if c['id']=='bun': log[c['id']]=dict(deg=cur,note='bun design value (not a clamp), unchanged'); continue
        if cur>=CAP: log[c['id']]=dict(deg=cur,note='at/above cap, unchanged'); continue
        lo=int(round(cur*10)); hi=int(round(CAP*10))
        c['maxSwayDeg']=hi/10
        if ok(): lo=hi
        else:
            c['maxSwayDeg']=lo/10
            if not ok(): log[c['id']]=dict(deg=cur,note='current value already hits, left for validate --fix'); continue
            while hi-lo>1:
                m=(lo+hi)//2; c['maxSwayDeg']=m/10
                if ok(): lo=m
                else: hi=m
        c['maxSwayDeg']=lo/10; log[c['id']]=dict(deg=lo/10,frm=cur,limited_by=None if lo==int(round(CAP*10)) else 'eye/mouth 2px margin')
        print(v,c['id'],cur,'->',lo/10,flush=True)
    # final check of every swaying part
    log['_final_hits']={e['id']:H_(e) for e in sw}
    out[v]=dict(before=before,after={e['id']:e['maxSwayDeg'] for e in sw},log=log)
    print(v,'final hits',log['_final_hits'],flush=True)
    if WRITE: json.dump(RIG,open(f'{hd}/rig.json','w'),indent=1)
json.dump(out,open('/tmp/unclamp_result.json','w'),indent=1)
