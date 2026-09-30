# Measurements: source anger mouth (emotions/anger.png) and our front rest mouths. Read-only.
import json,sys; import numpy as np; from PIL import Image; from scipy import ndimage as ndi
sys.path.insert(0,'/workspace/shadowveil/mouth/work'); from lipmask import load, lip_mask
SRC='/workspace/shadowveil/reference/grok_build/public/puppet/emotions/anger.png'
def src_mask():
    A=np.array(Image.open(SRC).convert('RGBA')).astype(float); rgb=A[...,:3]; L=rgb@[.299,.587,.114]
    y0,y1,x0,x1=395,480,300,445
    win=np.zeros(L.shape,bool); win[y0:y1,x0:x1]=True
    brown=(rgb[...,0]-rgb[...,2]>25)&(L>20)
    dark=win&(L<70)&~brown
    lab,n=ndi.label(dark); sz=ndi.sum(dark,lab,range(1,n+1)); core=lab==(1+int(np.argmax(sz)))
    core=ndi.binary_fill_holes(ndi.binary_closing(core,iterations=1))
    return A,L,core
def line_runs(L,mask,cols,thr):
    """vertical run lengths of dark (L<thr) pixels inside mask per column: returns list of runs per column"""
    out=[]
    for x in cols:
        col=(L[:,x]<thr)&mask[:,x]; lab,n=ndi.label(col); out.append([int((lab==i).sum()) for i in range(1,n+1)])
    return out
if __name__=='__main__':
    A,L,core=src_mask(); ys,xs=np.nonzero(core)
    x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max(); cx=(x0+x1)/2
    # seam: darkest row near centre columns in the lower-middle of the mask
    cols=range(int(cx)-3,int(cx)+4)
    seam=np.mean([y0+np.argmin(L[y0:y1+1,x]) for x in cols])
    # corners: leftmost / rightmost mask pixel rows
    lc=ys[xs==x0].mean(); rc=ys[xs==x1].mean()
    # nose tip / bottom: bright highlight + nostrils; take lowest nostril dark pixel above mouth
    nos=(L<60); nos[:, :]&=False
    nosreg=(L[380:412,330:410]<60); nyy,nxx=np.nonzero(nosreg)
    rep=dict(src=SRC,maskPx=int(core.sum()),bbox=[int(x0),int(y0),int(x1),int(y1)],W=int(x1-x0+1),H=int(y1-y0+1),centreX=float(cx),seamY=float(seam),
             cornerL=[int(x0),float(lc)],cornerR=[int(x1),float(rc)],tiltDeg=float(np.degrees(np.arctan2(rc-lc,x1-x0))),
             upAbove=float(seam-y0),downBelow=float(y1-seam),nostrilBottomY=float(380+nyy.max()) if len(nyy) else None,
             topLineRuns=line_runs(L,core,[int(cx)-20,int(cx)+20],40),seamRuns=line_runs(L,core,list(cols),15))
    print(json.dumps(rep,indent=1)); json.dump(rep,open('tmp/src_meas.json','w'),indent=1)
    np.save('tmp/src_core.npy',core)
    ours={}
    for v,g in {'apose':(681,289),'tpose':(684,281)}.items():
        b=load(v); M,D,skin=lip_mask(b,*g); rig=json.load(open(f'/workspace/shadowveil/views/{v}/mouth/rig.json'))
        Lb=b[...,:3]@[.299,.587,.114]; yd,xd=np.nonzero(D); ax,ay=rig['anchor']['x'],rig['anchor']['y']
        seamcols=list(range(ax-3,ax+4))
        ours[v]=dict(anchor=[ax,ay],drawnBBox=[int(xd.min()),int(yd.min()),int(xd.max()),int(yd.max())],W=int(xd.max()-xd.min()+1),H=int(yd.max()-yd.min()+1),
                     upAbove=float(ay-yd.min()),downBelow=float(yd.max()-ay),seamRuns=line_runs(Lb,D,seamcols,45),skin=[float(c) for c in skin],
                     seamRunsLoose=line_runs(Lb,D,seamcols,60))
        np.save(f'tmp/D_{v}.npy',D)
    print(json.dumps(ours,indent=1)); json.dump(ours,open('tmp/ours_meas.json','w'),indent=1)
