# sharpness of head+neck part pixels vs shoulder band (torso px within 70 px below the neck base) around head-axis toggles
import json,sys,os,numpy as np
from PIL import Image
from scipy import ndimage as nd
ID='/workspace/shadowveil/rig/previews/idle/frames';VD='/workspace/shadowveil/views'
def run(name):
    d=json.load(open(name+'.check.json'));v=d['view'];R=d['rows']
    head=np.array(Image.open(f'{VD}/{v}/body/head.png').convert('RGBA'))[...,3]>0
    rig=json.load(open(f'{VD}/{v}/body/rig.json'));own=np.zeros_like(head)
    for o in ('hair','eyes','mouth','hands'):
        try: j=json.load(open(f'{VD}/{v}/{o}/rig.json'))
        except Exception: continue
        for p in (j if isinstance(j,list) else j.get('parts',[])):
            f=p.get('file') if isinstance(p,dict) else None
            if f and os.path.exists(f'{VD}/{v}/{o}/{f}'):
                a=np.array(Image.open(f'{VD}/{v}/{o}/{f}').convert('RGBA'))[...,3]
                if a.shape==head.shape: own|=a>0
    own=nd.binary_dilation(own,iterations=6)
    ys=np.nonzero(head.any(1))[0];nb=ys.max()
    neck=nd.binary_erosion(head,iterations=4)&~own; neck[:nb-80]=False      # lowest 80 rows of the head part = neck
    tors=np.array(Image.open(f'{VD}/{v}/body/torso.png').convert('RGBA'))[...,3]>0
    sh=nd.binary_erosion(tors,iterations=4)&~own&~head; sh[:nb+2]=False; sh[nb+72:]=False
    face=nd.binary_erosion(head,iterations=4)&~nd.binary_dilation(own&False,iterations=1); face[nb-80:]=False
    def S(im,m):
        L=im[...,:3].astype(np.float32)@np.array([.299,.587,.114],np.float32);g=np.hypot(nd.sobel(L,0),nd.sobel(L,1));a=im[...,3]==255;return float(g[m&a].mean())
    rest=np.array(Image.open(f'{ID}/{name}/rest.png'));b={k:S(rest,m) for k,m in (('head',face),('neck',neck),('shoulder',sh))}
    ax=[r['f'] for r in R if r['headAxis']];fs=sorted(set(f for a in ax for f in range(max(0,a-2),min(len(R),a+3))))
    out={}
    for f in fs:
        im=np.array(Image.open(f'{ID}/{name}/frames/f{f:04d}.png'));out[f]={k:round(S(im,m)/b[k],4) for k,m in (('head',face),('neck',neck),('shoulder',sh))}
        out[f]['axis']=R[f]['headAxis']
    return ax,out
if __name__=='__main__':
    res={}
    for n in sys.argv[1:]:
        ax,o=run(n);res[n]={'axis_frames':ax,'series':o}
        print(n,'axis frames',ax)
        for f,x in o.items(): print('  f%03d'%f,x)
    json.dump(res,open('flicker_'+sys.argv[1]+'.json','w'))
