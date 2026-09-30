# Focused crossfade / gap / ghost check on lossless harness PNG frames around each rest<->smile switch (keyed clips).
# Uses head transforms from the MP4 tracking pass (data/mp4_*.json) to stabilise; references are the clip's own held frames.
import sys,json,numpy as np,cv2
sys.path.insert(0,'/workspace/shadowveil/mouth/work/idle_qa')
from measure import setup,rgba_on_grey,load_crop,gray,GREY,IDLE,OUT
def stab(F,H): return cv2.warpAffine(F,H,(F.shape[1],F.shape[0]),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderValue=(GREY,)*3)
def Hof(x,d):
    # rebuild rest->frame affine from stored translation+angle (crop coords)
    th=np.radians(x['ang']);c,s=np.cos(th),np.sin(th);return np.array([[c,-s,x['hx']],[s,c,x['hy']]],np.float32)
def run(view,clip):
    S=setup(view);box=S['box'];d=json.load(open(f'{OUT}/mp4_{clip}_{view}.json'));fr=d['frames']
    meta=json.load(open(f'{IDLE}/frames/keys_{clip}_{view}/meta.json'))['frames']
    fd=f'{IDLE}/frames/keys_{clip}_{view}/frames'
    def get(f): return stab(rgba_on_grey(load_crop(f'{fd}/f{f:04d}.png',box)),Hof(fr[f],d))
    Rref=np.mean([get(f) for f in range(30,60,3)],0); Sref=np.mean([get(f) for f in range(95,135,4)],0)
    ra=S['shp']['rest'][...,3]; sa=S['shp']['smile'][...,3]
    uni=(ra>0)|(sa>0); corner=(sa>200)&(ra==0)
    win=S['mwin']
    Rl,Sl=gray(Rref),gray(Sref)
    sw=[i for i in range(1,len(meta)) if meta[i]['mouth']!=meta[i-1]['mouth']]
    res=[]
    for s0 in sw:
        for f in range(s0-1,s0+4):
            St=get(f); L=gray(St)
            D=(Sref-Rref)[win]; a=float(np.dot((St-Rref)[win].ravel(),D.ravel())/np.dot(D.ravel(),D.ravel()))
            dR=np.abs(St-Rref).max(2); dS=np.abs(St-Sref).max(2)
            mid=(np.minimum(dR,dS)>30)&win           # pixels matching neither held shape
            gap=uni&(L>np.maximum(Rl,Sl)+20)          # lighter than both shapes inside the mouth footprint = skin/base showing through
            # corners of the outgoing smile staying fully visible (smile->rest fade)
            cornerS=int((corner&(dS<12)&(dR>30)).sum()); cornerN=int(corner.sum())
            F=rgba_on_grey(load_crop(f'{fd}/f{f:04d}.png',box));b=F[...,2]-np.maximum(F[...,0],F[...,1])
            rt=meta[f]; alpha=None
            if rt['mouthT0']>-1e8: alpha=min(1,max(0,(rt['t']*1000-rt['mouthT0'])/60))
            res.append(dict(f=f,t_video=round(f/30,4),t_anim=rt['t'],rig=rt['mouth'],rigPrev=rt['mouthPrev'],rigAlpha=None if alpha is None else round(alpha,3),
                a=round(a,3),midPx=int(mid.sum()),gapPx=int(gap.sum()),cornerStillSmile=cornerS,cornerN=cornerN,blueMax=float(b[S['ring']].max())))
            print(view,clip,res[-1],flush=True)
            if f in (s0+1,):
                np.save(f'{OUT}/fade_{clip}_{view}_f{f:04d}.npy',np.stack([Rref,Sref,St]).astype(np.uint8))
    json.dump(res,open(f'{OUT}/fades_{clip}_{view}.json','w'))
if __name__=='__main__':
    for v in ['apose','tpose','left','right']:
        for c in ['idle_breathe','idle_weight_shift','idle_arm_settle']: run(v,c)
