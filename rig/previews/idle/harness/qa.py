# Per-frame QA of rendered idle frames (read-only analysis of the rig's output; never writes into views/ or the rig).
import json,sys,os,math
import numpy as np
from PIL import Image
from scipy import ndimage as nd
IDLE='/workspace/shadowveil/rig/previews/idle'
QA=sys.argv[2] if len(sys.argv)>2 else IDLE+'/qa'
name=sys.argv[1]; W_=os.environ.get('WORK',IDLE+'/work')+'/'+name
meta=json.load(open(W_+'/meta.json')); fps=meta['fps']
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1]; return x*x+y*y<=r*r
D3,D4,D2=disk(3),disk(4),disk(2)
rest=np.array(Image.open(W_+'/rest.png')); RA=rest[...,3]
ys,xs=np.nonzero(RA); pad=80
y0,y1,x0,x1=max(0,ys.min()-pad),min(RA.shape[0],ys.max()+pad),max(0,xs.min()-pad),min(RA.shape[1],xs.max()+pad)
def enclosed(op):
    lab,n=nd.label(~op); border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))
    keep=np.ones(n+1,bool); keep[list(border)]=False; keep[0]=False; return keep[lab]
def masks(A):
    op=A>=128
    enc=enclosed(op)
    cl=nd.binary_closing(op,structure=D3,border_value=0)
    tear=cl&~op&~enc   # thin cracks that a 3 px closing seals (not enclosed holes, counted separately)
    inner=nd.binary_erosion(op,structure=D4,border_value=0)
    seam=inner&(A<255)
    return op,enc,tear,seam
RAc=RA[y0:y1,x0:x1]; rop,renc,rtear,rseam=masks(RAc)
renc_d=nd.binary_dilation(renc,structure=D3); rtear_d=nd.binary_dilation(rtear,structure=D3); rseam_d=nd.binary_dilation(rseam,structure=D2)
bones=meta['info']['bones'] or []
VIEWD=f"/workspace/shadowveil/views/{meta['view']}"
def union(owner):
    try: j=json.load(open(f'{VIEWD}/{owner}/rig.json'))
    except Exception: return np.zeros(RA.shape,bool)
    ps=j if isinstance(j,list) else j.get('parts',[]); m=np.zeros(RA.shape,bool)
    for q in ps:
        f=q.get('file') if isinstance(q,dict) else None
        if f and os.path.exists(f'{VIEWD}/{owner}/{f}'):
            a=np.array(Image.open(f'{VIEWD}/{owner}/{f}').convert('RGBA'))[...,3]
            if a.shape==RA.shape: m|=a>0
    return m
HAIR=nd.binary_dilation(union('hair'),structure=disk(45))[y0:y1,x0:x1]
HANDS=nd.binary_dilation(union('hands'),structure=disk(12))[y0:y1,x0:x1]&~HAIR
BODYR=~HAIR&~HANDS
JOINTS=[b['id'] for b in bones if b['parent']]
def nearest_joint(py,px,fb):
    best=None
    for j in JOINTS:
        if j not in fb: continue
        d=math.hypot(fb[j][0]-px,fb[j][1]-py)
        if best is None or d<best[1]: best=(j,d)
    return best
# foot contact: sole = lowest opaque rows in the bottom band of the silhouette, split at the pelvis x
H_=RA.shape[0]; ybot=ys.max()
pel=[b for b in bones if b['id']=='pelvis']; pelx=pel[0]['pivot'][0] if pel else RA.shape[1]/2
def feet(A):
    out={}
    band=A[ybot-120:ybot+40]>=128
    for side,sl in (('xlo',slice(0,int(pelx))),('xhi',slice(int(pelx),A.shape[1]))):
        b=band[:,sl]; r=np.nonzero(b.any(1))[0]
        if not len(r): out[side]=None; continue
        low=r.max(); rows=b[max(0,low-5):low+1]; cx=np.nonzero(rows.any(0))[0]
        out[side]=dict(bottom=int(low+ybot-120),xmin=int(cx.min()+sl.start),xmax=int(cx.max()+sl.start),xc=float(cx.mean()+sl.start))
    return out
rest_feet=feet(RA); restLine=int(np.nonzero((RA>=128).any(1))[0].max())
rows=[];prev=None;prevA=None
fdir=W_+'/frames'; files=sorted(os.listdir(fdir))
for i,fn in enumerate(files):
    im=np.array(Image.open(f'{fdir}/{fn}')); A=im[...,3]; Ac=A[y0:y1,x0:x1]; fm=meta['frames'][i]
    op,enc,tear,seam=masks(Ac)
    nh=enc&~renc_d; nt=tear&~rtear_d; ns=seam&~rseam_d
    # tears at joints: within 60 px of a posed joint pivot
    jt={}
    pts=np.argwhere(nt&BODYR)
    if len(pts) and JOINTS:
        J=np.array([fm['bones'][j][:2] for j in JOINTS if j in fm['bones']]);JN=[j for j in JOINTS if j in fm['bones']]
        d=np.hypot(pts[:,1][:,None]+x0-J[None,:,0],pts[:,0][:,None]+y0-J[None,:,1]);k=d.argmin(1);dm=d.min(1)
        for kk,dd in zip(k,dm):
            if dd<=60: jt[JN[kk]]=jt.get(JN[kk],0)+1
    ft=feet(A)
    slide={}
    for s in ('xlo','xhi'):
        if ft[s] and rest_feet[s]: slide[s]=dict(dx=round(ft[s]['xc']-rest_feet[s]['xc'],2),dy=ft[s]['bottom']-rest_feet[s]['bottom'],dxmin=ft[s]['xmin']-rest_feet[s]['xmin'],dxmax=ft[s]['xmax']-rest_feet[s]['xmax'])
    chg=None
    if prevA is not None: chg=int((np.abs(im.astype(np.int16)-prev.astype(np.int16)).max(-1)>40).sum())
    rest_diff=int(((np.abs(im.astype(np.int16)-rest.astype(np.int16)).max(-1)>40)).sum())
    lost=int(((RAc>=128)&~op&~nd.binary_dilation(~rop,structure=disk(6))).sum())  # deep-interior rest pixels now background (interior loss)
    bbox=None
    bad=(nh|nt|ns)&BODYR
    if not bad.any(): bad=(nh|nt|ns)&HANDS
    if not bad.any(): bad=nh|nt|ns
    if bad.any():
        lab,n=nd.label(nd.binary_dilation(bad,structure=disk(8))); cnt=nd.sum(bad,lab,range(1,n+1)); big=int(np.argmax(cnt))+1
        yy,xx=np.nonzero(bad&(lab==big)); bbox=[int(xx.min()+x0),int(yy.min()+y0),int(xx.max()+x0),int(yy.max()+y0)]
    byreg=lambda m:dict(body=int((m&BODYR).sum()),hands=int((m&HANDS).sum()),hair=int((m&HAIR).sum()))
    hr=fm['bones'].get('head') or fm['bones'].get('torso'); headAxis=bool(hr and abs(hr[2])<0.01)
    line=int(np.nonzero((A>=128).any(1))[0].max())
    rows.append(dict(frame=i,t=fm['t'],holesBy=byreg(nh),tearsBy=byreg(nt),seamBy=byreg(ns),headAxisAligned=headAxis,footLine=line,footLift=restLine-line,newHoles=int(nh.sum()),holeComps=int(nd.label(nh)[1]),newTears=int(nt.sum()),tearsAtJoints=jt,newSeamAlpha=int(ns.sum()),interiorLost=lost,
        guard=fm['err'],missing=fm['issues'],mouth=fm['mouth'],feet=slide,changedPx=chg,restDiffPx=rest_diff,bbox=bbox))
    prev=im;prevA=A
    if i%40==0: print(name,i,rows[-1]['newHoles'],rows[-1]['newTears'],rows[-1]['newSeamAlpha'],flush=True)
# mouth shape holds as displayed at 30 fps
runs=[];cur=None;n=0
for r in rows:
    if r['mouth']==cur: n+=1
    else:
        if cur is not None: runs.append((cur,n))
        cur=r['mouth'];n=1
inner_runs=runs[1:] if len(runs)>1 else []
holds=meta['holds']
# joint motion: local angle per bone (world - parent world), velocity/accel in deg/s
byb={b['id']:b for b in bones}; ang={}
for b in bones:
    if not b['parent']: continue
    s=[f['bones'][b['id']][2]-(f['bones'][b['parent']][2] if b['parent'] in f['bones'] else 0) for f in meta['frames']]
    s=np.array(s); vel=np.diff(s)*fps; acc=np.diff(vel)*fps
    ang[b['id']]=dict(param=b['param'],range=round(float(s.max()-s.min()),3),min=round(float(s.min()),3),max=round(float(s.max()),3),maxVel=round(float(np.abs(vel).max()),2) if len(vel) else 0,maxAcc=round(float(np.abs(acc).max()),1) if len(acc) else 0)
agg=lambda key:{r:max(x[key][r] for x in rows) for r in ('body','hands','hair')}
aggn=lambda key:{r:sum(x[key][r]>0 for x in rows) for r in ('body','hands','hair')}
summary=dict(view=meta['view'],name=name,keys=meta.get('keys'),holesMaxBy=agg('holesBy'),holesFramesBy=aggn('holesBy'),tearsMaxBy=agg('tearsBy'),tearsFramesBy=aggn('tearsBy'),seamMaxBy=agg('seamBy'),seamFramesBy=aggn('seamBy'),
  headSharpToggles=sum(rows[i]['headAxisAligned']!=rows[i-1]['headAxisAligned'] for i in range(1,len(rows))),headAxisFrames=sum(r['headAxisAligned'] for r in rows),
  footLiftMax=max(r['footLift'] for r in rows),footLiftMaxAt=max(rows,key=lambda r:r['footLift'])['t'],footLiftMin=min(r['footLift'] for r in rows),frames=len(rows),seconds=meta['seconds'],seed=meta['seed'],hairOverride=meta.get('hairOverride'),
  maxNewHoles=max(r['newHoles'] for r in rows),framesWithNewHoles=sum(r['newHoles']>0 for r in rows),
  maxNewTears=max(r['newTears'] for r in rows),framesWithNewTears=sum(r['newTears']>0 for r in rows),
  tearsAtJointsTotal={k:sum(r['tearsAtJoints'].get(k,0) for r in rows) for k in set(k for r in rows for k in r['tearsAtJoints'])},
  maxNewSeamAlpha=max(r['newSeamAlpha'] for r in rows),framesWithSeamAlpha=sum(r['newSeamAlpha']>0 for r in rows),
  maxInteriorLost=max(r['interiorLost'] for r in rows),
  guardViolations=len(meta['errs']),guardSamples=meta['errs'][:3],missingParts=sorted(set(meta['issues'])|set(x for r in rows for x in r['missing'])),
  mouthSwitchesSim=len(holds),minHoldSimMs=round(min(holds),1) if holds else None,minHoldDisplayedFrames=min(n for _,n in inner_runs) if inner_runs else None,
  mouthRuns=len(runs),
  footSlide={s:dict(maxAbsDx=max(abs(r['feet'][s]['dx']) for r in rows if s in r['feet']),maxAbsDy=max(abs(r['feet'][s]['dy']) for r in rows if s in r['feet']),
     maxEdgeShift=max(max(abs(r['feet'][s]['dxmin']),abs(r['feet'][s]['dxmax'])) for r in rows if s in r['feet'])) for s in ('xlo','xhi') if any(s in r['feet'] for r in rows)},
  jointMotion=ang,logs=[l for l in meta['logs'] if not l.startswith('warn: Canvas2D')],motionQuality=meta.get('motionQuality'),
  maxChangedPx=max((r['changedPx'] or 0) for r in rows),medChangedPx=float(np.median([r['changedPx'] for r in rows if r['changedPx'] is not None])))
score=lambda r:(r['holesBy']['body']+r['tearsBy']['body']+r['seamBy']['body']+r['interiorLost'],r['holesBy']['hands']+r['tearsBy']['hands']+r['seamBy']['hands'],r['newHoles']+r['newTears']+r['newSeamAlpha'],r['restDiffPx'])
worst=max(rows,key=score); summary['worst']=dict(frame=worst['frame'],t=worst['t'],newHoles=worst['newHoles'],newTears=worst['newTears'],newSeamAlpha=worst['newSeamAlpha'],interiorLost=worst['interiorLost'],restDiffPx=worst['restDiffPx'],bbox=worst['bbox'],tearsAtJoints=worst['tearsAtJoints'],
  holesBy=worst['holesBy'],tearsBy=worst['tearsBy'],seamBy=worst['seamBy'],reason='body-region defect pixels' if score(worst)[0]>0 else 'hand-region defect pixels (no body-region defects in any frame)' if score(worst)[1]>0 else 'hair-region only' if score(worst)[2]>0 else 'no defect pixels in any frame; picked frame farthest from rest (max changed px vs rest)')
# crop of the worst frame, composited on flat mid-grey (no markings drawn on her); defect mask saved as a separate PNG
im=Image.open(f'{fdir}/{files[worst["frame"]]}'); g=Image.new('RGBA',im.size,(128,128,128,255)); g.alpha_composite(im)
if worst['bbox']:
    bx=worst['bbox']; cx0,cy0,cx1,cy1=bx[0]-80,bx[1]-80,bx[2]+80,bx[3]+80
else:
    d=(np.abs(np.array(im).astype(np.int16)-rest.astype(np.int16)).max(-1)>40); d=nd.binary_opening(d,structure=D2)
    yy,xx=np.nonzero(d)
    if len(yy):
        # densest 400x400 window of change
        hy,hx=np.histogram2d(yy,xx,bins=[np.arange(0,im.size[1]+100,100),np.arange(0,im.size[0]+100,100)])
        sm=nd.uniform_filter(hy,size=4,mode='constant'); iy,ix=np.unravel_index(sm.argmax(),sm.shape); cy,cx=iy*100+50,ix*100+50
        cx0,cy0,cx1,cy1=cx-220,cy-220,cx+220,cy+220
    else: cx0,cy0,cx1,cy1=0,0,im.size[0],im.size[1]
cx0,cy0=max(0,cx0),max(0,cy0);cx1,cy1=min(im.size[0],cx1),min(im.size[1],cy1)
os.makedirs(f'{QA}',exist_ok=True)
crop=g.crop((cx0,cy0,cx1,cy1)).convert('RGB'); sc=2 if crop.size[0]<500 else 1
crop.resize((crop.size[0]*sc,crop.size[1]*sc),Image.NEAREST).save(f'{QA}/{name}_worst_f{worst["frame"]:04d}_t{worst["t"]:.3f}s.png')
restc=Image.new('RGBA',im.size,(128,128,128,255)); restc.alpha_composite(Image.open(W_+'/rest.png'))
restc.crop((cx0,cy0,cx1,cy1)).convert('RGB').resize((crop.size[0]*sc,crop.size[1]*sc),Image.NEAREST).save(f'{QA}/{name}_worst_f{worst["frame"]:04d}_REST_same_crop.png')
summary['worst']['crop']=f'{QA}/{name}_worst_f{worst["frame"]:04d}_t{worst["t"]:.3f}s.png'; summary['worst']['cropBox']=[cx0,cy0,cx1,cy1]
json.dump(dict(summary=summary,frames=rows),open(f'{QA}/{name}_qa.json','w'),indent=1)
print(json.dumps({k:v for k,v in summary.items() if k not in ('jointMotion','motionQuality')},indent=1))
