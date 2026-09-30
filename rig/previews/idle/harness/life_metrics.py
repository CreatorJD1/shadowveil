# motion ranges per Life system from a render's meta (params + bones), foot slide/lift from frames, interior partial alpha
import json,sys,os,numpy as np
from PIL import Image
sys.path.insert(0,os.path.dirname(__file__))
from alpha_interior import interior_partial
def run(d):
    m=json.load(open(d+'/meta.json'));F=m['frames'];P=lambda k:np.array([f['params'].get(k,0) for f in F])
    rng=lambda x:[round(float(x.min()),3),round(float(x.max()),3)]
    out={'view':m['view'],'frames':len(F)}
    deg={'BodyLean':8,'HeadTilt':8,'HeadNod':6}
    pr={}
    for k in ['BodyLean','HeadTilt','HeadNod','ShoulderL','ShoulderR','ElbowL','ElbowR','WristL','WristR','HipL','HipR','KneeL','KneeR','AnkleL','AnkleR','RootX','RootY','EyeBallX','EyeBallY','MouthForm','MouthOpen','HandLIndex','HandRIndex','HandLThumb']:
        x=P(k);pr[k]=dict(range=rng(x),p2p=round(float(x.max()-x.min()),3))
        if k in deg: pr[k]['p2pDeg']=round(float(x.max()-x.min())*deg[k],2)
        elif k.startswith(('Shoulder','Elbow','Hip','Knee','Ankle','Wrist')): pr[k]['p2pDeg']=round(float(x.max()-x.min())*25,2)
    out['params']=pr
    # bone world angles from meta (skin bones: [x,y,deg])
    B={}
    for b in F[0]['bones']:
        a=np.array([f['bones'][b][2] for f in F]);xy=np.array([f['bones'][b][:2] for f in F])
        B[b]=dict(angP2P=round(float(a.max()-a.min()),2),pivotPxP2P=[round(float(xy[:,0].max()-xy[:,0].min()),1),round(float(xy[:,1].max()-xy[:,1].min()),1)])
    out['bones']=B
    # knee image-plane kink: shin world - thigh world
    for s in 'LR':
        if f'shin_{s}' in F[0]['bones']:
            k=np.array([f['bones'][f'shin_{s}'][2]-f['bones'][f'thigh_{s}'][2] for f in F]);out[f'kneeKinkDeg_{s}']=rng(k)
    # mouth switches / blinks
    ms=[f['mouth'] for f in F];out['mouthSwitches']=sum(1 for a,b in zip(ms,ms[1:]) if a!=b);out['mouthShapes']=sorted(set(ms))
    eo=P('EyeLOpen');t=np.array([f['t'] for f in F]);st=[];prev=False
    for i,x in enumerate(eo):
        c=x<0.5
        if c and not prev: st.append(round(float(t[i]),3))
        prev=c
    out['blinkStarts(open<0.5)']=st;out['blinkGapsS']=[round(b-a,2) for a,b in zip(st,st[1:])];out['shutFrames(open<0.5)']=int((eo<0.5).sum())
    # feet from frames: bottom band per foot (split at pelvis x), lowest opaque row and sole centre x, vs rest
    rest=np.array(Image.open(d+'/rest.png'))[...,3];H=rest.shape[0]
    def feet(a,cx=None):
        ys,xs=np.nonzero(a>=128);y1=ys.max();band=(ys>=y1-25);bx=xs[band];by=ys[band]
        cx=np.median(bx) if cx is None else cx;res={}
        for s,sel in (('A',bx<cx),('B',bx>=cx)):
            if sel.sum()<20: continue
            res[s]=dict(bottom=int(by[sel].max()),xc=float(bx[sel].mean()),xmin=int(bx[sel].min()),xmax=int(bx[sel].max()))
        return res,cx
    rf,CX=feet(rest);sl={};lift=[]
    ip=[];ip240=[]
    for i,f in enumerate(sorted(os.listdir(d+'/frames'))):
        a=np.array(Image.open(d+'/frames/'+f))[...,3];ft,_=feet(a,CX)
        for s in ft:
            if s in rf: sl.setdefault(s,[]).append((ft[s]['xmin']-rf[s]['xmin'],ft[s]['xmax']-rf[s]['xmax'],ft[s]['bottom']-rf[s]['bottom']))
        if i%4==0:
            n,_,_=interior_partial(a);ip.append(n);ip240.append(interior_partial.lt240)
    out['footSlide']={s:dict(maxAbsToeHeelDxPx=int(max(max(abs(q[0]),abs(q[1])) for q in v)),maxLiftPx=int(max(-q[2] for q in v)),maxSinkPx=int(max(q[2] for q in v))) for s,v in sl.items()}
    out['interiorPartialAlpha']=dict(sampledEvery=4,max=int(max(ip)),mean=round(float(np.mean(ip)),1),max_lt240=int(max(ip240)),mean_lt240=round(float(np.mean(ip240)),1))
    return out
if __name__=='__main__':
    res={}
    for a in sys.argv[2:]:
        n,d=a.split('=',1);res[n]=run(d);r=res[n];print(n,'root',r['params']['RootX']['range'],r['params']['RootY']['range'],'feet',r['footSlide'],'ipa',r['interiorPartialAlpha'],'mouth',r['mouthSwitches'],flush=True)
    json.dump(res,open(sys.argv[1],'w'),indent=1)
