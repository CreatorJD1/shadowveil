# Read-only mouth QA for Shadowveil idle renders. Reads MP4 (primary) or the harness PNG frames (lossless cross-check),
# one frame at a time from a small head crop. Writes only JSON into mouth/work/idle_qa/data.
import sys, os, json, subprocess, numpy as np, cv2
from PIL import Image
SV='/workspace/shadowveil'; IDLE=SV+'/rig/previews/idle'; OUT=SV+'/mouth/work/idle_qa/data'
NOSE={'apose':(680,262),'tpose':(680,256),'left':(580,240),'right':(792,245)}
SHAPES=['rest','M','smile','AA','EE','OH','OH_half','AA_half','EE_half']
GREY=128.0
def rgba_on_grey(a):
    a=a.astype(np.float32); al=a[...,3:4]/255.0; return a[...,:3]*al+GREY*(1-al)
def load_crop(path,box):
    x0,y0,x1,y1=box; im=Image.open(path).convert('RGBA').crop((x0,y0,x1,y1)); return np.array(im)
def gray(rgb): return (rgb[...,:3].astype(np.float32)@np.array([.299,.587,.114],np.float32))
def setup(view):
    rj=json.load(open(f'{SV}/views/{view}/mouth/rig.json')); ax,ay=rj['anchor']['x'],rj['anchor']['y']
    box=(ax-180,ay-230,ax+180,ay+110)
    rest=load_crop(f'{IDLE}/frames/{view}/rest.png',box)  # rig's own render(g,true) at rest
    R=rgba_on_grey(rest)
    shp={s:load_crop(f'{SV}/views/{view}/mouth/{s}.png',box) for s in SHAPES}
    comp={s:(shp[s][...,:3]*(shp[s][...,3:4]/255.)+R*(1-shp[s][...,3:4]/255.)) for s in SHAPES}  # shape over rest render (approx)
    occ=np.zeros(R.shape[:2],bool)
    for o in ('hair','eyes','mouth','hands'):
        d=f'{SV}/views/{view}/{o}'
        for fn in sorted(os.listdir(d)):
            if fn.endswith('.png') and 'chroma' not in fn:
                a=load_crop(f'{d}/{fn}',box)[...,3]; occ|=a>0
    face=(rest[...,3]==255)&~cv2.dilate(occ.astype(np.uint8),np.ones((11,11),np.uint8)).astype(bool)
    face[ay-box[1]+25:,:]=False   # nothing below the chin line (neck/chest skin deforms)
    mu=np.zeros_like(face)
    for s in SHAPES: mu|=shp[s][...,3]>0
    mwin=cv2.dilate(mu.astype(np.uint8),np.ones((7,7),np.uint8)).astype(bool)
    ring=cv2.dilate(mu.astype(np.uint8),np.ones((21,21),np.uint8)).astype(bool)  # mouth + ~10px fringe for chroma scan
    return dict(view=view,anchor=(ax,ay),box=box,R=R,rest=rest,shp=shp,comp=comp,face=face,mwin=mwin,ring=ring)
def frames_mp4(path,box,W=1366,H=1740):
    x0,y0,x1,y1=box; w,h=x1-x0,y1-y0
    p=subprocess.Popen(['nice','-n','10','ffmpeg','-v','error','-threads','2','-i',path,'-vf',f'crop={w}:{h}:{x0}:{y0}','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    n=w*h*3
    while True:
        b=p.stdout.read(n)
        if len(b)<n: break
        yield np.frombuffer(b,np.uint8).reshape(h,w,3).astype(np.float32)
    p.wait()
def frames_png(d,box):
    for fn in sorted(os.listdir(d+'/frames')):
        yield rgba_on_grey(load_crop(d+'/frames/'+fn,box))
def ecc(tmpl,inp,mask,warp,mode):
    crit=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,200,1e-6)
    try: cc,w=cv2.findTransformECC(tmpl,inp,warp.copy(),mode,crit,mask.astype(np.uint8),3); return cc,w
    except cv2.error: return -1,warp
def gradmag(g): return np.hypot(cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3),cv2.Sobel(g,cv2.CV_32F,0,1,ksize=3))
def run(view,src,label):
    S=setup(view); ax,ay=S['anchor']; x0,y0,_,_=S['box']
    Rg=gray(S['R']); face=S['face']; mwin=S['mwin']
    it=frames_mp4(src,S['box']) if src.endswith('.mp4') else frames_png(src,S['box'])
    Wm=np.eye(2,3,dtype=np.float32); out=[]
    k=np.ones((3,3),np.uint8)
    mmask={s:cv2.dilate((S['shp'][s][...,3]==255).astype(np.uint8),k) for s in SHAPES}
    compg={s:gray(S['comp'][s]) for s in SHAPES}
    gref={s:float(gradmag(compg[s])[mwin].mean()) for s in SHAPES}
    headref=float(gradmag(Rg)[face].mean())
    nx,ny=NOSE[view]; nmask=np.zeros(face.shape,np.uint8); nmask[ny-y0-15:ny-y0+15,nx-x0-18:nx-x0+18]=1
    lipc=np.array([ax-x0,ay-y0],np.float32)
    for f,F in enumerate(it):
        Fg=gray(F)
        # head: frame(x) ~ rest(Wm x); template=frame, input=rest, mask on rest-face
        cc,Wm=ecc(Fg,Rg,face,Wm,cv2.MOTION_EUCLIDEAN)
        H=cv2.invertAffineTransform(Wm)  # rest->frame
        ang=float(np.degrees(np.arctan2(H[1,0],H[0,0])))
        pa=H[:,:2]@lipc+H[:,2]  # predicted mouth anchor in frame
        St=cv2.warpAffine(F,H,(F.shape[1],F.shape[0]),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderValue=(GREY,GREY,GREY))
        Sg=gray(St)
        # nearest shape (least RMS in mouth window) and rest<->smile blend
        rms={s:float(np.sqrt(((St-S['comp'][s])[mwin]**2).mean())) for s in SHAPES}
        best=min(rms,key=rms.get)
        Rr,Ss=S['comp']['rest'][mwin],S['comp']['smile'][mwin]; D=(Ss-Rr).ravel(); a=float(np.dot((St[mwin]-Rr).ravel(),D)/np.dot(D,D))
        blend=(1-np.clip(a,0,1))*Rr+np.clip(a,0,1)*Ss; brms=float(np.sqrt(((St[mwin]-blend)**2).mean()))
        # mouth drift vs head: translation of the mouth patch in head-stabilised coords
        tgt=best if best in SHAPES else 'rest'
        cm,Tm=ecc(Sg,compg[tgt],mmask[tgt],np.eye(2,3,dtype=np.float32),cv2.MOTION_TRANSLATION)
        dx,dy=float(-Tm[0,2]),float(-Tm[1,2])  # mouth offset in head coords (+ = mouth moved right/down relative to head)
        cn,Tn=ecc(Sg,Rg,nmask,np.eye(2,3,dtype=np.float32),cv2.MOTION_TRANSLATION); ndx,ndy=float(-Tn[0,2]),float(-Tn[1,2])
        # chroma blue in raw frame, mouth + 10px ring (placed by head transform)
        ringF=cv2.warpAffine(S['ring'].astype(np.uint8),H,(F.shape[1],F.shape[0]),flags=cv2.INTER_NEAREST).astype(bool)
        r,g,b=F[...,0],F[...,1],F[...,2]; blue=(b-np.maximum(r,g)>60)&(b>100)
        bl=np.argwhere(blue&ringF)
        # residual pixels in the mouth window that match neither the shape nor the rest/smile blend (gap / ghost / skin)
        if a>0.02 and a<0.98 and best in('rest','smile'): ref=blend.reshape(-1,3)
        else: ref=S['comp'][best][mwin]
        dev=np.abs(St[mwin]-ref).max(1); bad=int((dev>60).sum())
        # sharpness: raw-frame gradient in head face mask and mouth window (masks moved with the head)
        GM=gradmag(Fg)
        fm=cv2.warpAffine(face.astype(np.uint8),H,(F.shape[1],F.shape[0]),flags=cv2.INTER_NEAREST).astype(bool)
        mw=cv2.warpAffine(mwin.astype(np.uint8),H,(F.shape[1],F.shape[0]),flags=cv2.INTER_NEAREST).astype(bool)
        out.append(dict(f=f,cc=round(float(cc),5),hx=round(float(H[0,2]),3),hy=round(float(H[1,2]),3),ang=round(ang,4),
            ax=round(float(pa[0]+x0),3),ay=round(float(pa[1]+y0),3),mcc=round(float(cm),5),mdx=round(dx,3),mdy=round(dy,3),ncc=round(float(cn),5),ndx=round(ndx,3),ndy=round(ndy,3),
            best=best,rms={k2:round(v2,2) for k2,v2 in rms.items()},a=round(a,4),brms=round(brms,2),bad=bad,
            blue=int(len(bl)),blueMax=float((b-np.maximum(r,g))[ringF].max()),
            sharpHead=round(float(GM[fm].mean())/headref,4),sharpLip=round(float(GM[mw].mean())/gref[best],4)))
    json.dump(dict(view=view,src=src,label=label,box=S['box'],anchor=S['anchor'],frames=out),open(f'{OUT}/{label}.json','w'))
    fr=out; sw=sum(1 for i in range(1,len(fr)) if fr[i]['best']!=fr[i-1]['best'])
    print(label,'n',len(fr),'switches',sw,'maxdrift',round(max(np.hypot(x['mdx'],x['mdy']) for x in fr),3),'minHeadCC',min(x['cc'] for x in fr),'blue',sum(x['blue'] for x in fr),flush=True)
if __name__=='__main__':
    run(sys.argv[1],sys.argv[2],sys.argv[3])
