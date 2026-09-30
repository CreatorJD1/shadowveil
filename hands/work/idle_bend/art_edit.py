# Hidden-art cleanup. Only writes (a) palm pixels covered at rest by an alpha-255 hand part drawn above the palm, (b) Ring1 f1/f2 frame pixels (never drawn at rest).
# Backs up every changed PNG to art_backup/<view>__<file> (first time only). Flat colours (rig.json skinRGB/lineRGB), alpha 255 or 0, no blue.
import json,os,shutil,sys,numpy as np
from PIL import Image
from scipy import ndimage as nd
from qalib import *
ROOT='/workspace/shadowveil';BK='/workspace/shadowveil/hands/work/idle_bend/art_backup'
log=[];DRY=os.environ.get('DRY')  # DRY=<dir>: write to <dir>/<view>/ instead of views (no backup)
def backup(view,fn):
    src=f'{ROOT}/views/{view}/hands/{fn}';dst=f'{BK}/{view}__{fn}'
    if not os.path.exists(dst): shutil.copy2(src,dst)
def load(view,fn): return np.array(Image.open(f'{ROOT}/views/{view}/hands/{fn}').convert('RGBA'))
def save(view,fn,a,orig,note):
    n=int((np.abs(a.astype(int)-orig.astype(int)).max(-1)>0).sum())
    if n==0: return
    if DRY:
        os.makedirs(f'{DRY}/{view}',exist_ok=True);Image.fromarray(a).save(f'{DRY}/{view}/{fn}')
    else:
        backup(view,fn);Image.fromarray(a).save(f'{ROOT}/views/{view}/hands/{fn}')
    log.append(dict(view=view,file=fn,changedPx=n,note=note));print(view,fn,n,note)
def cover(view,S,j):
    c=np.zeros((1739,1365),bool)
    for p in j['parts']:
        if p.get('file') and p['id'].startswith(S+'_') and not p['id'].endswith('_palm'): c|=load(view,p['file'])[...,3]==255
    return c
from palm_hidden import analyse
for view,runs in [('tpose',['renders/dense_before/tpose']),('apose',['renders/dense_before/apose'])]:
    j=json.load(open(f'{ROOT}/views/{view}/hands/rig.json'))
    for S in 'LR':
        skin=np.array(j['hands'][S]['skinRGB'],np.uint8)
        pf=f'{S}_palm.png';P0=load(view,pf);P=P0.copy();C=cover(view,S,j);A=P0[...,3]
        R=analyse(view,S,runs,C,A)
        trim=R['poke']&~R['use']                      # hidden palm px that only ever show outside the posed silhouette
        near=nd.binary_dilation(A==255,structure=disk(3))
        gap=R['gap']&~R['poke']&near&~(R['expf2']&(A==0))                   # hidden, not-opaque palm spots next to the palm that show inside the silhouette -> flat skin
        if view!='tpose': trim=np.zeros_like(trim)     # apose: hidden palm fill also draws the f2 fist bottom contour -> fill only, never trim
        dark=P0[...,:3].astype(int).sum(-1)<330
        clean=R['use']&~R['edge']&~R['poke']&dark&(view=='tpose')      # hidden fill-outline strokes that show inside the silhouette, never on its edge -> flat skin
        P[trim]=0;P[gap|clean,:3]=skin;P[gap|clean,3]=255
        lab,n=nd.label(P[...,3]>0,structure=np.ones((3,3)));sz=nd.sum(P[...,3]>0,lab,range(1,n+1))
        for k in np.nonzero(sz<25)[0]:
            cm=lab==k+1
            if (cm<=C).all() and not (cm&~((A>0)&C)).any(): P[cm]=0; trim|=cm   # tiny hidden palm islands left over -> cleared
        assert not ((np.abs(P.astype(int)-P0.astype(int)).max(-1)>0)&~C).any(),'edit outside rest-covered area'
        save(view,pf,P,P0,f'hidden palm: {int(trim.sum())} px poking outside the posed silhouette cleared, {int(gap.sum())} gap px filled flat skin, {int(clean.sum())} exposed hidden-outline px -> flat skin')
# 3) tpose Ring1 f1/f2 trims
T=json.load(open('trim_tpose.json'))
for fn,d in T.items():
    a0=load('tpose',fn);a=a0.copy()
    for x,y in d['trim']: a[y,x]=0
    save('tpose',fn,a,a0,f"Ring1 filler trimmed: {len(d['trim'])} px that stuck out of the silhouette / showed over the palm")
json.dump(log,open('art_edit_log_dry.json' if DRY else 'art_edit_log.json','w'),indent=1)
