"""Task 2: render worst sim frames with real hair PNGs + rig pivots (per-part drives, chained), check eye/mouth crossing
and revealed skin/white/holes where swaying hair moved away. Writes only into hair/qa/export_check/."""
import sys,json,math,glob,gc; sys.dont_write_bytecode=True
sys.path.insert(0,'/workspace/shadowveil/hair/qa/export_check')
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from sim import *
BOX=(520,20,840,380)
def rotAt(px,py,deg):
    t=math.radians(deg); c,s=math.cos(t),math.sin(t); return (c,s,-s,c,px-c*px+s*py,py-s*px-c*py)
def warp(img,M,box):
    x0,y0,x1,y1=box; a,b,c,d,e,f=M
    oy,ox=np.mgrid[y0:y1,x0:x1].astype(np.float32); ox+=0.5; oy+=0.5
    det=a*d-b*c; X=ox-e; Y=oy-f; sx=(d*X-c*Y)/det-0.5; sy=(-b*X+a*Y)/det-0.5
    return np.stack([ndi.map_coordinates(img[...,k],[sy,sx],order=1,mode='constant',cval=0) for k in range(4)],-1)
def load(p):
    a=np.array(Image.open(p).convert('RGBA')).astype(np.float32); a[...,:3]*=a[...,3:]/255; return a
def over(d,s): return s+d*(1-s[...,3:]/255)
def pose_mats(parts,drv,ymax):
    by={p['id']:p for p in parts}; M={}
    def m(i):
        if i in M: return M[i]
        p=by[i]; q=p.get('parent'); base=m(q) if q and q in by else (1,0,0,1,0,0)
        x=drv.get(i,(0,0))[0]; M[i]=mul(base,rotAt(p['pivotX'],p['pivotY'],(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)*x)); return M[i]
    out={}
    for p in parts:
        y=drv.get(p['id'],(0,0))[1]; dy=math.floor(clamp(y,-1,1)*clamp(p.get('swayY') or 0,0,1)*ymax+0.5)
        out[p['id']]=mul((1,0,0,1,0,dy),m(p['id']))
    return out
def composite(v,parts,imgs,bb,face,Ms):
    x0,y0,x1,y1=BOX; can=np.zeros((y1-y0,x1-x0,4),np.float32); above=np.zeros(can.shape[:2],np.float32); swa=np.zeros_like(above)
    order=sorted(enumerate(parts),key=lambda t:(t[1]['layer'],t[0]))
    for _,p in order:
        if p['layer']<200: w=warp(imgs[p['id']],Ms[p['id']],BOX); can=over(can,w)
    can=over(can,bb); can=over(can,face)
    for _,p in order:
        if p['layer']>=200:
            w=warp(imgs[p['id']],Ms[p['id']],BOX); can=over(can,w); above=np.maximum(above,w[...,3])
            if (p.get('swayWeight') or 0)>0: swa=np.maximum(swa,w[...,3])
    return can,above,swa
def classify(rgb,a):
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    hole=a<128; white=(~hole)&(np.minimum(np.minimum(r,g),b)>200)
    skin=(~hole)&(~white)&(r>95)&(r>g)&(g>b)&(r-b>30)
    return hole,white,skin
def run():
    R=json.load(open(OUT+'/sim_results.json')); res={}; tiles=[]
    for v in VIEWS:
        V=load_view(v); parts=V['hair']; ymax=json.load(open(f'{ROOT}/views/{v}/hair/rig.json')).get('swayYMaxPx',0)
        imgs={p['id']:load(f'{ROOT}/views/{v}/hair/{p["file"]}') for p in parts}
        x0,y0,x1,y1=BOX
        bb=load(f'{ROOT}/views/{v}/base_body.png')[y0:y1,x0:x1]
        face=np.zeros_like(bb); forb=np.zeros(bb.shape[:2],bool)
        fs=[f for f in sorted(glob.glob(f'{ROOT}/views/{v}/eyes/Eye*_white.png'))+sorted(glob.glob(f'{ROOT}/views/{v}/eyes/Eye*_lid_0.png'))+sorted(glob.glob(f'{ROOT}/views/{v}/eyes/Eye*_lash.png'))+glob.glob(f'{ROOT}/views/{v}/mouth/rest.png')]
        for f in fs: face=over(face,load(f)[y0:y1,x0:x1])
        for sub in ('eyes','mouth'):
            for f in glob.glob(f'{ROOT}/views/{v}/{sub}/*.png'):
                if 'chroma' in f: continue
                forb|=np.array(Image.open(f).convert('RGBA'))[y0:y1,x0:x1,3]>0
        forb2=ndi.binary_dilation(forb,iterations=2)
        rest,ab0,sw0=composite(v,parts,imgs,bb,face,pose_mats(parts,{},ymax))
        # poses: worst sim frame per setting (max sum |x| over swaying parts, any clip/mode), + envelope corners
        poses=[]
        for sn in SETTINGS:
            best=None
            for r in R:
                if r['view']!=v or r['setting']!=sn: continue
                tot=sum(abs(p['peakDeg'])/max(p['limEff'],1e-9) for p in r['parts'].values())
                if best is None or tot>best[0]: best=(tot,r)
            r=best[1]; dur,fps,frames=clip_frames(r['clip']); loops=1 if dur>1 else 3
            drive=lambda t:head_pose(V,sample(frames,fps,dur,t-4.0) if 0<=t-4.0<dur*loops else dict(torso=0,hinge=0,neck=0,head=0),r['mode'])
            rec=simulate(V,SETTINGS[sn],drive,4.0+dur*loops+5.0)
            for sgn in (-1,1):
                t,hp,o=max(rec,key=lambda q:sum(sgn*q[2][k][0] for k in q[2]))
                u=t-4.0; fr=f"f{int(u*fps)%len(frames)} loop{int(u//dur)}" if 0<=u<dur*loops else (f"rest+{u-dur*loops:.2f}s" if u>=0 else "preroll(wind)")
                poses.append((f"{sn} {r['clip']}/{r['mode']} {fr} ({'-' if sgn<0 else '+'})",{k:(o[k][0],o[k][3]) for k in o}))
        for sx in (-1,1):
            for sy in (-1,1):
                poses.append((f"envelope s={sx:+d} sy={sy:+d}",{p['id']:(sx,sy) for p in parts if (p.get('swayWeight') or 0)>0}))
        res[v]=[]
        for name,drv in poses:
            can,ab,swa=composite(v,parts,imgs,bb,face,pose_mats(parts,drv,ymax))
            a=can[...,3]; rgb=np.where(a[...,None]>0,can[...,:3]*255/np.maximum(a[...,None],1e-6),0)
            cross=(swa>0)&forb; cross2=(swa>0)&forb2
            revealed=(sw0>127)&(ab<128)
            hole,white,skin=classify(rgb,a)
            filled=ndi.binary_fill_holes(a>=128); enc=revealed&(a<128)&filled
            rh,rw,rs=revealed&hole,revealed&white,revealed&skin
            ys,xs=np.nonzero(rs|rh|rw)
            rec_=dict(pose=name,eye_mouth_overlap_px=int(cross.sum()),within2px=int(cross2.sum()),revealed_px=int(revealed.sum()),
                      revealed_hole_px=int(rh.sum()),enclosed_hole_px=int(enc.sum()),revealed_white_px=int(rw.sum()),revealed_skin_px=int(rs.sum()),
                      revealed_bbox=[int(xs.min()+x0),int(ys.min()+y0),int(xs.max()+x0),int(ys.max()+y0)] if len(xs) else None,
                      angles={k:round(((next(p for p in parts if p['id']==k).get('swayWeight') or 0)*(next(p for p in parts if p['id']==k).get('maxSwayDeg') or 0))*d[0],2) for k,d in drv.items()})
            res[v].append(rec_)
            if not name.startswith('envelope') or name.endswith('sy=+1') and 's=-1' in name or name.endswith('sy=-1') and 's=+1' in name:
                im=np.clip(rgb*(a[...,None]/255)+np.array([60,150,60])*(1-a[...,None]/255),0,255).astype(np.uint8)
                im[forb2&~cross2]=(im[forb2&~cross2]*0.5+np.array([0,200,255])*0.5).astype(np.uint8)
                im[cross2]=[255,0,0]; im[rs]=[255,0,255]; im[rh|rw]=[255,255,0]; im[enc]=[255,128,0]
                tiles.append((v,name,Image.fromarray(im)))
        print(v,[(q['pose'][:28],q['eye_mouth_overlap_px'],q['within2px'],q['revealed_skin_px'],q['revealed_hole_px'],q['enclosed_hole_px'],q['revealed_white_px']) for q in res[v]],flush=True)
        del imgs,bb,face; gc.collect()
    json.dump(res,open(OUT+'/frame_check.json','w'),indent=1)
    # contact sheet: rows=views, cols=rest? poses
    cols=max(sum(1 for t in tiles if t[0]==v) for v in VIEWS); tw,th=(BOX[2]-BOX[0])//2,(BOX[3]-BOX[1])//2
    sheet=Image.new('RGB',(cols*tw,len(VIEWS)*(th+24)+30),(20,20,20)); D=ImageDraw.Draw(sheet)
    D.text((4,4),'worst sim frames per setting (+/- sign) & envelope corners. red=hair on eye/mouth(+2px), cyan=eye/mouth zone, magenta=revealed skin, yellow=revealed bg/white, orange=enclosed hole',fill=(255,255,255))
    for ri,v in enumerate(VIEWS):
        row=[t for t in tiles if t[0]==v]
        for ci,(_,name,im) in enumerate(row):
            X,Y=ci*tw,30+ri*(th+24); sheet.paste(im.resize((tw,th)),(X,Y+24)); D.text((X+2,Y+2),v+': '+name[:30],fill=(255,255,0)); D.text((X+2,Y+12),name[30:60],fill=(255,255,0))
    sheet.save(OUT+'/worst_frames_sheet.png'); print('sheet',sheet.size)
run()
