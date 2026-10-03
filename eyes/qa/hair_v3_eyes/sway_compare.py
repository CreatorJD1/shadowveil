"""Diagonal eyes (staged, after lash trim) vs Base Hair v3 (hair/staged/diagonals_v3, read-only) in VIEW space (1365x1739).
Base = her turn frame (f033/f191) mapped with the eyes' viewFit (nearest, as hair/.../work/common.py). Eye parts (frame px) mapped the same way.
Hair: contract sec.4 slider path - every part's s = HairSwayX; angle = swayWeight*maxSwayDeg*s about its pivot, chained through parent
(own rotation, then each ancestor); dy = round(HairSwayY*swayY*swayYMaxPx), not inherited. No hair renderer exists in diagonals_v3, so this is a
Python mirror: inverse-mapped nearest sampling (hard alpha, like the v3 files). Layers < 400 (hair_back, bun) are behind the body and skipped.
Draw order: frame, per eye white(+iris atop, gaze shift), lid_k, lash (layers 400-413), then hair parts by layer (600+).
Metrics in a window = eye workRegion mapped to view, padded 30 px:
  lash_vis_on_src_hair : lash px visible (not under hair) where her frame draws hair (Base Hair key rule) - must be 0
  lash_under_hair      : lash px covered by a hair part (hidden by z-order; info)
  hair_over_opening    : hair px over visible eye white/iris (white|iris not covered by lid/lash)
  holes_trim           : trimmed lash px (view) covered by neither hair nor any eye part (would show the face base)
Two hair variants: 'v3' = files as staged; 'v3_refill_sim' = in-memory only (nothing written to hair/): each v3 part gets back its
v2 pre_eyecut px (alpha>=128, raw colour, alpha 255) at the trimmed lash px - a projection of what build_v3.py would restore if rerun with the
trimmed lash in the opening (the real rebuild also palette-snaps / iris-tone filters)."""
import json, glob, math, numpy as np, sys
from PIL import Image, ImageDraw
R='/workspace/shadowveil'; D=f'{R}/eyes/staged/diagonals'; HV=f'{R}/hair/staged/diagonals_v3'; BK=f'{D}/backups_lash_hair_trim'
W,H=1365,1739; FR={'045':'f033','315':'f191'}
A=lambda p:np.array(Image.open(p).convert('RGBA'))
rnd=lambda z:int(math.floor(z+.5))
def f2v(fm,fit,win):
    s,dx,dy=fit; x0,y0,x1,y1=win; yy,xx=np.mgrid[y0:y1,x0:x1]
    fx=np.floor((xx+.5-dx)/s).astype(int); fy=np.floor((yy+.5-dy)/s).astype(int)
    ok=(fx>=0)&(fx<fm.shape[1])&(fy>=0)&(fy<fm.shape[0]); out=np.zeros((y1-y0,x1-x0)+fm.shape[2:],fm.dtype); out[ok]=fm[fy[ok],fx[ok]]; return out
def shiftv(a,dx,dy):
    o=np.zeros_like(a); h,w=a.shape[:2]; o[max(0,dy):h+min(0,dy),max(0,dx):w+min(0,dx)]=a[max(0,-dy):h+min(0,-dy),max(0,-dx):w+min(0,-dx)]; return o
def over(d,s):
    a=s[...,3:4]/255.; o=d.astype(float).copy(); o[...,:3]=s[...,:3]*a+d[...,:3]*(1-a); o[...,3]=np.maximum(d[...,3],s[...,3]); return o.astype(np.uint8)
res={'doc':__doc__}; tiles={}
for ang in ('045','315'):
    rig=json.load(open(f'{D}/{ang}/rig.json')); vf=rig['viewFit']; fit=(vf['scale'],vf['dx'],vf['dy'])
    a0,b0,a1,b1=rig['workRegion']; win=(int(fit[0]*a0+fit[1])-30,int(fit[0]*b0+fit[2])-30,int(fit[0]*(a1+1)+fit[1])+30,int(fit[0]*(b1+1)+fit[2])+30)
    x0,y0,x1,y1=win
    fr=A(f'{R}/reference/apose_turn/frames/{FR[ang]}.png'); base=f2v(fr,fit,win)
    key=(base[...,3]>0)&(base[...,2].astype(int)-np.maximum(base[...,0],base[...,1])>60)
    P={e:{n:f2v(A(f'{D}/{ang}/{e}_{n}.png'),fit,win) for n in ['white','iris','lash']+[f'lid_{k}' for k in range(8)]} for e in rig['eyes']}
    trim=np.zeros(key.shape,bool)
    for f in glob.glob(f'{BK}/{ang}/*_lash.png'):
        e=f.split('/')[-1].split('_')[0]; P[e]['lash_pre']=f2v(A(f),fit,win); trim|=(P[e]['lash_pre'][...,3]>0)&(P[e]['lash'][...,3]==0)
    hr=json.load(open(f'{HV}/{ang}/hair/rig.json')); parts=[q for q in hr['parts'] if q['layer']>=400]; by={q['id']:q for q in hr['parts']}; ymax=hr.get('swayYMaxPx',0)
    HI0={q['id']:A(f'{HV}/{ang}/hair/{q["file"]}') for q in parts}
    trimv=np.zeros((H,W),bool); tv=trim; trimv[y0:y1,x0:x1]=tv
    HIR={}
    for q in parts:
        a=HI0[q['id']].copy(); pe=A(f'{R}/hair/staged/diagonals_v2/pre_eyecut/{ang}/{q["file"]}'); m=trimv&(pe[...,3]>=128)&(a[...,3]==0)
        a[m]=pe[m]; a[m,3]=255; HIR[q['id']]=a
    HI=HI0
    yy,xx=np.mgrid[y0:y1,x0:x1]; cx0=xx+.5; cy0=yy+.5
    def hair(sx,sy):
        cv=np.zeros((y1-y0,x1-x0,4),np.uint8); m=np.zeros(cv.shape[:2],bool)
        for q in sorted(parts,key=lambda q:q['layer']):
            ch=[]; c=q
            while c is not None: ch.append(c); c=by.get(c.get('parent'))
            X=cx0.copy(); Y=cy0-rnd(sy*(q.get('swayY') or 0)*ymax)
            for c in reversed(ch):   # undo root-most first
                t=-np.deg2rad((c.get('swayWeight') or 0)*(c.get('maxSwayDeg') or 0)*sx)
                if t==0: continue
                px,py=c['pivotX'],c['pivotY']; u=X-px; v=Y-py; X=px+u*np.cos(t)-v*np.sin(t); Y=py+u*np.sin(t)+v*np.cos(t)
            xi=np.floor(X).astype(int); yi=np.floor(Y).astype(int); ok=(xi>=0)&(xi<W)&(yi>=0)&(yi<H)
            s=np.zeros_like(cv); s[ok]=HI[q['id']][yi[ok],xi[ok]]; cv=over(cv,s); m|=s[...,3]>0
        return cv,m
    def eyes(k,gx,gy,pre=False):
        cv=base.copy(); lash=np.zeros(key.shape,bool); op=np.zeros(key.shape,bool); anyp=np.zeros(key.shape,bool)
        for e in rig['eyes']:
            l=rig['irisLimitsPx'][e]; dx=rnd(gx*(l['dxAtXplus1'] if gx>0 else -l['dxAtXminus1'])); dy=rnd(gy*(l['dyAtYplus1'] if gy>0 else -l['dyAtYminus1']))
            wv=P[e]['white']; ir=shiftv(f2v(A(f'{D}/{ang}/{e}_iris.png'),(fit[0],fit[1]+dx*fit[0],fit[2]+dy*fit[0]),win),0,0)
            ir[...,3]=np.where(wv[...,3]>0,ir[...,3],0); lay=over(wv,ir)
            ls=P[e]['lash_pre'] if (pre and 'lash_pre' in P[e]) else P[e]['lash']; ld=P[e][f'lid_{k}']
            for s in (lay,ld,ls): cv=over(cv,s); anyp|=s[...,3]>0
            op|=(lay[...,3]>0); op&=~(ld[...,3]>0); op&=~(ls[...,3]>0)
            lash&=~(ld[...,3]>0); lash|=ls[...,3]>0
        return cv,lash,op,anyp
    for VAR,HI in (('v3',HI0),('v3_refill_sim',HIR)):
      out={}; H0={}
      for sx in (-1,-.5,0,.5,1):
          for sy in (-1,0,1):
              H0[(sx,sy)]=hair(sx,sy)
      for (sx,sy),(hc,hm) in H0.items():
          for k in (0,7):
              for g in ((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1)):
                  cv,lash,op,anyp=eyes(k,*g); img=over(cv,hc)
                  r=dict(lash_vis_on_src_hair=int((lash&~hm&key).sum()),lash_under_hair=int((lash&hm).sum()),hair_over_opening=int((hm&op).sum()),
                         holes_trim=int((trim&~hm&~anyp).sum()))
                  out[f'X{sx:+.1f} Y{sy:+d} lid{k} gaze{g[0]:+d},{g[1]:+d}']=r
                  if g==(0,0) and sy==0: tiles[(ang,VAR,sx,k)]=(img,hm,lash,op,anyp)
      # pre-trim reference at rest + eyes-only
      for pre in (True,False):
          cv,lash,op,anyp=eyes(0,0,0,pre); hc,hm=H0[(0,0)]
          out['REST eyes-only '+('PRE-trim' if pre else 'post-trim')]=dict(lash_vis_on_src_hair=int((lash&key).sum()),eye_diff_vs_frame_view=int((cv[...,:3]!=base[...,:3]).any(-1).sum()))
          out['REST +hair '+('PRE-trim' if pre else 'post-trim')]=dict(lash_vis_on_src_hair=int((lash&~hm&key).sum()),holes_trim=int((trim&~hm&~anyp).sum()),
              trim_px_covered_by_hair=int((trim&hm).sum()),hair_over_opening=int((hm&op).sum()))
          tiles[(ang,VAR,'pre' if pre else 'post')]=(over(cv,hc),hm,lash,op,anyp)
      tiles[(ang,'src')]=(base,None,None,None,None); tiles[(ang,'trim')]=trim; tiles[(ang,'key')]=key; tiles[(ang,'win')]=win
      agg={m:max(v[m] for kk,v in out.items() if not kk.startswith('REST')) for m in ('lash_vis_on_src_hair','lash_under_hair','hair_over_opening','holes_trim')}
      attr={}; allp=parts
      for (sx,sy) in H0:
          for q in allp:
              parts=[q]; _,m1=hair(sx,sy); parts=allp
              n=max(int((m1&eyes(0,*g)[2]).sum()) for g in ((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1)))
              if n: attr[f'X{sx:+.1f} Y{sy:+d} {q["id"]}']=n
      res.setdefault(ang,{})[VAR]={'hair_over_opening_by_part_max_gaze':attr,'window_view_xyxy':win,'trim_view_px':int(trim.sum()),'max_over_all_states':agg,'states':out}
      print(ang,VAR,'trim_view_px',int(trim.sum()),'max',agg); print('  attr',attr)
      for kk in out:
          if kk.startswith('REST') or ('Y+0' in kk and 'gaze+0,+0' in kk): print('  ',kk,out[kk])
json.dump(res,open('sway_compare.json','w'),indent=1)
# sheet: crop around trimmed px, 8x nearest
Z=8; rows=[]
for ang in ('045','315'):
    tr=tiles[(ang,'trim')]; ys,xs=np.nonzero(tr); cy,cx=int(ys.mean()),int(xs.mean()); c=(slice(max(0,cy-22),cy+22),slice(max(0,cx-28),cx+28))
    for VAR in ('v3','v3_refill_sim'):
        seq=[('src frame','src'),(f'PRE-trim +{VAR} X0','pre'),(f'POST-trim +{VAR} X0','post')]+[(f'{VAR} X{sx:+.1f} lid{k}',(ang,VAR,sx,k)) for k in (0,7) for sx in (-1,-.5,0,.5,1)]
        row=[]
        for lab,t in seq:
            img,hm,lash,op,anyp=tiles[(ang,t)] if t=='src' else tiles[(ang,VAR,t)] if isinstance(t,str) else tiles[t]; im=img[c][...,:3].copy()
            if hm is not None:
                hole=(tr&~hm&~anyp)[c]; im[hole]=(255,0,255); im[(hm&op)[c]]=(0,255,255); im[(lash&~hm&tiles[(ang,'key')])[c]]=(255,255,0)
            I=Image.fromarray(im).resize((im.shape[1]*Z,im.shape[0]*Z),Image.NEAREST)
            if t=='src':
                d=ImageDraw.Draw(I); yy2,xx2=np.nonzero(tr[c])
                for y,x in zip(yy2,xx2): d.rectangle([x*Z,y*Z,x*Z+Z-1,y*Z+Z-1],outline=(255,0,255))
            C=Image.new('RGB',(I.width,I.height+18),'white'); C.paste(I,(0,18)); ImageDraw.Draw(C).text((3,3),f'{ang} {lab}',fill=(0,0,0)); row.append(np.array(C))
            row.append(np.full((C.height,6,3),255,np.uint8))
        rows.append(np.concatenate(row[:8*2],1)); rows.append(np.concatenate(row[8*2:],1))
rows=[r for r in rows if r is not None]; Wm=max(r.shape[1] for r in rows)
rows=[np.pad(r,((0,8),(0,Wm-r.shape[1]),(0,0)),constant_values=255) for r in rows]
leg=Image.new('RGB',(Wm,22),'white'); ImageDraw.Draw(leg).text((4,5),'magenta = trimmed lash px uncovered (hole; on src tile: outline of trimmed px)  cyan = hair over visible white/iris  yellow = lash visible where her frame draws hair.  view px, 8x nearest',fill=(0,0,0))
Image.fromarray(np.concatenate([np.array(leg)]+rows,0)).save('eyes_vs_hair_v3_zoom.png'); print('sheet written')
