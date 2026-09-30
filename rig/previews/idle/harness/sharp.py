# sharpness time series of the torso+head (skin that rides the torso), excluding eyes/mouth/hair/hands owner regions.
# S_t = mean gradient magnitude of luminance inside the region, relative to rest. Flicker events = sign changes of the
# frame-to-frame sharpness step where the step exceeds 1.5% of rest (sharp->soft->sharp pulses), plus count of frames >3% sharper than their +-5 frame median.
import sys,os,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
def region(view,shape):
    VD=f'/workspace/shadowveil/views/{view}';m=np.zeros(shape,bool)
    for o in ('hair','hands','eyes','mouth'):
        try: j=json.load(open(f'{VD}/{o}/rig.json'))
        except Exception: continue
        for p in (j if isinstance(j,list) else j.get('parts',[])):
            fn=p.get('file') if isinstance(p,dict) else None
            if fn and os.path.exists(f'{VD}/{o}/{fn}'):
                a=np.array(Image.open(f'{VD}/{o}/{fn}').convert('RGBA'))[...,3]
                if a.shape==shape: m|=a>0
    return ~nd.binary_dilation(m,iterations=25)
def S(im,reg):
    L=im[...,:3].astype(np.float32)@np.array([.299,.587,.114],np.float32);g=np.hypot(nd.sobel(L,0),nd.sobel(L,1));return float(g[reg].mean())
def run(fd,view):
    rest=np.array(Image.open(fd+'/rest.png'));A=rest[...,3]
    reg=region(view,A.shape)&nd.binary_erosion(A==255,iterations=6)
    ys,xs=np.nonzero(reg);ymax=ys.min()+int(0.45*(ys.max()-ys.min()));reg[ymax:]=False  # upper body: chest, neck, face, upper arms
    s0=S(rest,reg);fs=sorted(os.listdir(fd+'/frames'));out=[]
    try: M=json.load(open(fd+'/meta.json'))['frames']
    except Exception: M=[]
    for i,f in enumerate(fs):
        im=np.array(Image.open(fd+'/frames/'+f))
        if i<len(M):  # undo the whole-px root translation so the fixed rest region sees the same body area
            p=M[i].get('params',{});dx=int(round(p.get('RootX',0) or 0));dy=int(round(p.get('RootY',0) or 0))
            if dx or dy: im=np.roll(im,(-dy,-dx),axis=(0,1))
        a=im[...,3]
        out.append(S(im,reg&(a==255))/s0)
    x=np.array(out);d=np.diff(x);big=np.abs(d)>0.015;sg=np.sign(d)*big
    rev=0;last=0
    for v in sg:
        if v!=0:
            if last!=0 and v!=last: rev+=1
            last=v
    med=nd.median_filter(x,size=11,mode='nearest');spk=int((x-med>0.03).sum())
    return dict(meanRel=round(float(x.mean()),4),min=round(float(x.min()),4),max=round(float(x.max()),4),p2p=round(float(x.max()-x.min()),4),maxStep=round(float(np.abs(d).max()),4),bigSteps=int(big.sum()),pulseReversals=rev,sharpSpikes=spk,series=[round(float(v),4) for v in x])
if __name__=='__main__':
    res={}
    for spec in sys.argv[2:]:
        name,fd,view=spec.split(':');r=run(fd,view);res[name]=r;print(name,{k:v for k,v in r.items() if k!='series'},flush=True)
    json.dump(res,open(sys.argv[1],'w'))
