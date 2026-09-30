# Base Hair lineart-under-deformation check (READ-ONLY on the hair it inspects; writes only to --out).
#   python3 lineart_check.py --tag live|staged --hairroot <dir with <view>/hair> --out <dir> [--crops N]
# Mirror of the renderer (hair/tools/render.py: chained rotAt matrices, bilinear drawImage), uniform HairSwayX=s for all parts,
# HairSwayY=0, s in {-1,-0.5,+0.5,+1} vs rest. Line ink = alpha>=96 and max(r,g,b)<=60 after un-premultiply.
# (1) width: per part rendered alone; at every rest skeleton point of a line section (<=6 px wide) the coverage width = ink mass
#     (alpha x dark) in a 3 px disk / skeleton px in the disk; the disk is carried by the part's own transform to the sway image
#     (bilinear). PASS if p95 |dw| <= 1 px
#     and (strands/tips) the part's ink component count (>=6 px) does not grow. Ink = alpha>=96 & max(r,g,b)<=60 (outline core <=18 for
#     hair_front/hair_back/bun, whose fill is navy).
# (2) breaks: per joint (child pivot, carried by the parent's matrix), hair-only composite in a 25x25 window; the child's ink and
#     the parent's ink within 6 px of the pivot must be in ONE 8-connected ink component whenever they are at rest.
#     FAIL also if the window's ink component count (>=6 px) grows (a line piece split off). Endpoints: reported only.
# (3) kinks: alpha-0.5 contour of the hair-only composite in the window, resampled at ~1 px; turning angle over 3 px arms.
#     A sway contour point with turning >60 deg is a NEW sharp corner if neither the child's nor the parent's inverse
#     transform maps it within 2 px of a rest contour point with turning >=30 deg. Also reported: relative rotation at the seam.
import sys, os, json, argparse, numpy as np
sys.path.insert(0,'/workspace/shadowveil/hair/tools'); import render as RD
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage.morphology import skeletonize
from skimage.measure import find_contours
ap=argparse.ArgumentParser(); ap.add_argument('--tag'); ap.add_argument('--hairroot'); ap.add_argument('--out'); ap.add_argument('--crops',type=int,default=0)
ap.add_argument('--bodyroot',default='/workspace/shadowveil/views'); a=ap.parse_args()
V=['apose','tpose','left','right','back']; SS=[-1,-0.5,0.5,1]; RW=12; SHARP=60
AMIN=96; DARK=60; DARK_MASS=18; MASS={'hair_front','hair_back','bun'}
def ink(u,dark=DARK): return (u[...,3]>=AMIN)&(u[...,:3].max(-1)<=dark)
def local_widths(L):
    sk=skeletonize(L); e=ndi.distance_transform_edt(np.pad(L,1))[1:-1,1:-1]; ys,xs=np.nonzero(sk); return xs,ys,2*e[sk]-1
def matched_delta(U0,Us,dk,Mr,Msw,box,thin=6,r=3):
    # coverage width: at each rest skeleton point of a line section (<=thin px), effective width = ink mass (alpha x dark) in a
    # radius-r disk / skeleton px in that disk. Sway: same disk carried by the part's own transform (rigid: same skeleton length).
    L0=ink(U0,dk); xr,yr,wr=local_widths(L0); keep=wr<=thin; xr,yr=xr[keep],yr[keep]
    if not len(xr): return None
    sk=np.zeros(L0.shape,bool); sk[yr,xr]=True
    m0=U0[...,3]/255*(U0[...,:3].max(-1)<=dk); ms=Us[...,3]/255*(Us[...,:3].max(-1)<=dk)
    Hh,Ww=L0.shape; M=Msw; iv=inv(Mr); dw=[]
    yy,xx=np.mgrid[-r-1:r+2,-r-1:r+2]; disk=np.hypot(xx,yy)<=r
    for x,y in zip(xr,yr):
        if x<r+2 or y<r+2 or x>=Ww-r-2 or y>=Hh-r-2: continue
        cnt=sk[y-r-1:y+r+2,x-r-1:x+r+2][disk].sum(); w0=m0[y-r-1:y+r+2,x-r-1:x+r+2][disk].sum()/cnt
        X,Y=apply(M,*apply(iv,x+box[0]+.5,y+box[1]+.5)); X-=box[0]+.5; Y-=box[1]+.5
        # disk at the carried centre, sampled with bilinear interpolation of the sway ink mass
        cy,cx=Y+yy[disk],X+xx[disk]
        w1=ndi.map_coordinates(ms,[cy,cx],order=1,mode='constant').sum()/cnt
        dw.append(w1-w0)
    if not dw: return None
    dw=np.array(dw)
    return dict(p95_abs=float(np.percentile(np.abs(dw),95)),max_abs=float(np.abs(dw).max()),frac_gt1=float((np.abs(dw)>1).mean()),median=float(np.median(dw)),n=int(len(dw)))
def width_stats(L):
    if L.sum()<3: return None
    sk=skeletonize(L); e=ndi.distance_transform_edt(np.pad(L,1))[1:-1,1:-1]; w=2*e[sk]-1
    return dict(median=float(np.median(w)),p10=float(np.percentile(w,10)),p90=float(np.percentile(w,90)),ink_px=int(L.sum()))
def ncomp(L,minpx=3):
    lab,n=ndi.label(L,structure=np.ones((3,3))); s=ndi.sum(np.ones_like(lab),lab,range(1,n+1)); return int((np.array(s)>=minpx).sum()) if n else 0
def endpoints(L):
    sk=skeletonize(L); nb=ndi.convolve(sk.astype(int),np.ones((3,3)),mode='constant')-sk
    return int((sk&(nb==1)).sum())
def apply(M,x,y): return M[0]*x+M[2]*y+M[4], M[1]*x+M[3]*y+M[5]
def inv(M):
    a,b,c,d,e,f=M; det=a*d-b*c; ia,ib,ic,id_=d/det,-b/det,-c/det,a/det
    return [ia,ib,ic,id_,-(ia*e+ic*f),-(ib*e+id_*f)]
def contour_pts(alpha):
    out=[]
    for c in find_contours(np.pad(alpha,1),0.5):
        c=c-1
        if len(c)<8: continue
        seg=np.r_[0,np.cumsum(np.hypot(*np.diff(c,axis=0).T))]; L_=seg[-1]
        if L_<8: continue
        t=np.arange(0,L_,1.0); ys=np.interp(t,seg,c[:,0]); xs=np.interp(t,seg,c[:,1]); P=np.c_[xs,ys]
        closed=np.hypot(*(c[0]-c[-1]))<1.5
        for i in range(len(P)):
            if closed: p0,p2=P[(i-3)%len(P)],P[(i+3)%len(P)]
            else:
                if i<3 or i+3>=len(P): continue
                p0,p2=P[i-3],P[i+3]
            v1=P[i]-p0; v2=p2-P[i]; n1,n2=np.hypot(*v1),np.hypot(*v2)
            if n1<1e-6 or n2<1e-6: continue
            ang=np.degrees(np.arccos(np.clip(v1@v2/(n1*n2),-1,1))); out.append((P[i][0],P[i][1],ang))
    return np.array(out).reshape(-1,3)
res={}; crops_todo=[]
for v in V:
    hd=f'{a.hairroot}/{v}/hair'; parts,ymax=RD.load_rig(v,hd); by={p['id']:p for p in parts}
    imgs={p['id']:RD.premul(np.array(Image.open(f"{hd}/{p['file']}").convert('RGBA'))) for p in parts}
    H,W=next(iter(imgs.values())).shape[:2]
    order=[p for _,p in sorted(enumerate(parts),key=lambda t:(t[1]['layer'],t[0]))]
    Ms={s:RD.matrices(parts,ymax,s,0) for s in [0]+SS}
    rv=res[v]={'parts':{},'joints':{}}
    # (1) width per part (static parts too: hair_front edge, hair_back). Mass parts: outline core = max(r,g,b)<=DARK_MASS.
    for p in parts:
        al=imgs[p['id']][...,3]>0; ys,xs=np.nonzero(al)
        if not len(xs): continue
        dk=DARK_MASS if p['id'] in MASS else DARK
        box=(max(0,xs.min()-40),max(0,ys.min()-40),min(W,xs.max()+41),min(H,ys.max()+41))
        U0=RD.unpremul(RD.warp(imgs[p['id']],Ms[0][p['id']],box)); L0=ink(U0,dk); c0=ncomp(L0,6); r0=width_stats(L0)
        mass0=float((U0[...,3]/255*(U0[...,:3].max(-1)<=dk)).sum())
        d={'rest':r0,'rest_components':c0,'sway':{}}; worst=0; ok=True
        for s in SS:
            Us=RD.unpremul(RD.warp(imgs[p['id']],Ms[s][p['id']],box)); Ls=ink(Us,dk); cs=ncomp(Ls,6)
            md=matched_delta(U0,Us,dk,Ms[0][p['id']],Ms[s][p['id']],box)
            massr=float((Us[...,3]/255*(Us[...,:3].max(-1)<=dk)).sum())/max(mass0,1e-9)
            d['sway'][str(s)]=dict(width_delta=md,components=cs,ink_mass_ratio=round(massr,3))
            if md:
                worst=max(worst,md['p95_abs'])
                if md['p95_abs']>1: ok=False
            if cs>c0 and p['id'] not in MASS: ok=False   # mass parts: the <=18 outline core is fragmentary; width only
        d['worst_p95_abs_width_delta_px']=round(worst,2); d['PASS']=ok; rv['parts'][p['id']]=d
    # (2)+(3) joints
    for p in parts:
        q=p.get('parent')
        if not q or q not in by or not p.get('swayWeight'): continue
        jr={'parent':q,'sway':{}}; ok=True; score=0
        def window(s):
            cx,cy=apply(Ms[s][q],p['pivotX'],p['pivotY']); x0,y0=int(round(cx))-RW,int(round(cy))-RW; box=(x0,y0,x0+2*RW+1,y0+2*RW+1)
            can=np.zeros((2*RW+1,2*RW+1,4))
            for e in order: can=RD.over(can,RD.warp(imgs[e['id']],Ms[s][e['id']],box))
            U=RD.unpremul(can); L=ink(U)
            ch=ink(RD.unpremul(RD.warp(imgs[p['id']],Ms[s][p['id']],box))); pa=ink(RD.unpremul(RD.warp(imgs[q],Ms[s][q],box)))
            yy,xx=np.mgrid[y0:y0+2*RW+1,x0:x0+2*RW+1]; near=np.hypot(xx+.5-cx,yy+.5-cy)<=6
            lab,_=ndi.label(L,structure=np.ones((3,3)))
            lc=set(np.unique(lab[ch&near&L]))-{0}; lp=set(np.unique(lab[pa&near&L]))-{0}
            conn=None if not lc or not lp else bool(lc&lp)
            cp=contour_pts(U[...,3]/255.0); cp[:,0]+=x0; cp[:,1]+=y0
            cp=cp[np.hypot(cp[:,0]-cx,cp[:,1]-cy)<=8]
            return dict(box=box,U=U,L=L,conn=conn,comps=ncomp(L,6),ends=endpoints(L),cp=cp,c=(cx,cy))
        w0=window(0); jr['rest']=dict(child_parent_ink_connected=w0['conn'],components=w0['comps'],endpoints=w0['ends'],
                                     max_turn_deg=round(float(w0['cp'][:,2].max()),1) if len(w0['cp']) else None)
        rest_corners=w0['cp'][w0['cp'][:,2]>=30]
        wins={0:w0}
        for s in SS:
            w=window(s); wins[s]=w
            new_sharp=0; worst_turn=float(w['cp'][:,2].max()) if len(w['cp']) else 0
            for x,y,t in w['cp']:
                if t<=SHARP: continue
                matched=False
                for key in (p['id'],q):
                    xr,yr=apply(Ms[0][key],*apply(inv(Ms[s][key]),x,y))
                    if len(rest_corners) and np.hypot(rest_corners[:,0]-xr,rest_corners[:,1]-yr).min()<=2: matched=True; break
                new_sharp+=not matched
            brk=(w0['conn'] is True and w['conn'] is not True)
            rel=round((p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)*s,2)
            jr['sway'][str(s)]=dict(child_parent_ink_connected=w['conn'],line_break=brk,components=w['comps'],components_delta=w['comps']-w0['comps'],
                                   endpoints=w['ends'],endpoints_delta=w['ends']-w0['ends'],max_turn_deg=round(worst_turn,1),new_sharp_corners=int(new_sharp),rel_rot_deg=rel)
            if brk or new_sharp>0 or w['comps']>w0['comps']: ok=False
            score=max(score,10*brk+new_sharp+max(0,w['comps']-w0['comps'])+max(0,w['ends']-w0['ends'])*0.5)
        jr['PASS']=ok; jr['score']=score; rv['joints'][f"{p['id']}<-{q}"]=jr
        crops_todo.append((score,v,p['id'],q,wins,not ok))
    print(a.tag,v,'parts fail',[k for k,x in rv['parts'].items() if not x['PASS']],'joints fail',[k for k,x in rv['joints'].items() if not x['PASS']],flush=True)
os.makedirs(a.out,exist_ok=True)
json.dump(res,open(f'{a.out}/lineart_{a.tag}.json','w'),indent=1)
if a.crops:
    Z=10; T=(2*RW+1)*Z; sel=sorted(crops_todo,key=lambda t:(-t[0],t[1],t[2]))
    pick=[t for t in sel if t[5]]+[t for t in sel if not t[5]]
    per_view={}
    chosen=[]
    for t in pick:
        if t[5] or per_view.get(t[1],0)<2: chosen.append(t); per_view[t[1]]=per_view.get(t[1],0)+1
    for score,v,cid,q,wins,fail in chosen[:max(a.crops,sum(1 for t in chosen if t[5]))]:
        bb=np.array(Image.open(f'{a.bodyroot}/{v}/base_body.png').convert('RGBA'))
        im=Image.new('RGB',(T*5,T*2+18),(255,255,255)); d=ImageDraw.Draw(im)
        for i,s in enumerate([0]+SS):
            w=wins[s]; x0,y0,x1,y1=w['box']
            body=RD.premul(bb[max(0,y0):y1,max(0,x0):x1]) if x0>=0 and y0>=0 else np.zeros((y1-y0,x1-x0,4))
            bg=np.zeros((y1-y0,x1-x0,4)); bg[...]=[0,0,255,255]
            top=RD.unpremul(RD.over(RD.over(bg,body),RD.premul(w['U'])))[...,:3]
            im.paste(Image.fromarray(top).resize((T,T),Image.NEAREST),(i*T,18))
            m=np.full(w['L'].shape+(3,),255,np.uint8); m[w['L']]=[0,0,0]
            ti=Image.fromarray(m).resize((T,T),Image.NEAREST); dd=ImageDraw.Draw(ti)
            cx,cy=w['c']; dd.ellipse([ (cx-x0-6)*Z,(cy-y0-6)*Z,(cx-x0+6)*Z,(cy-y0+6)*Z],outline=(0,160,0))
            for x,y,t in w['cp']:
                if t>SHARP: dd.rectangle([(x-x0)*Z-3,(y-y0)*Z-3,(x-x0)*Z+3,(y-y0)*Z+3],fill=(255,0,0))
            im.paste(ti,(i*T,18+T))
            lab='rest' if s==0 else f's={s:+g}'
            if s!=0:
                r=res[v]['joints'][f'{cid}<-{q}']['sway'][str(s)]; lab+=f" br={int(r['line_break'])} dC={r['components_delta']} sharp={r['new_sharp_corners']}"
            d.text((i*T+3,3),lab,fill=(0,0,0))
        fn=f"{a.out}/{a.tag}_{v}_{cid}__{q}_{'FAIL' if fail else 'pass'}.png"; im.save(fn); print('crop',fn)
