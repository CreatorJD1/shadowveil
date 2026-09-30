# Read-only measurement: live eye parts (views/<view>/eyes, rest pose) vs A-pose turn frame warped into view space.
import cv2, numpy as np, json, sys
from scipy import ndimage as ndi
T='eyes/work/handoff/tmp/'
AM=json.load(open('body_tools/work/apose_turn/angle_map.json'))['handoff']
WIN={('apose','EyeR'):(605,200,685,256),('apose','EyeL'):(680,200,762,256),
     ('left','EyeL'):(588,192,650,242),('right','EyeR'):(716,192,784,242)}
def load_rgba(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); return a[...,:3].astype(float),a[...,3].astype(float)/255
def over(dst,src,al): return src*al[...,None]+dst*(1-al[...,None])
def live_composite(v,e,region):
    x0,y0,x1,y1=region
    bc,ba=load_rgba('views/%s/base.png'%v); base=over(np.full_like(bc,255),bc,ba)[y0:y1,x0:x1]
    out=base.copy()
    wc,wa=[q[y0:y1,x0:x1] for q in load_rgba('views/%s/eyes/%s_white.png'%(v,e))]
    ic,ia=[q[y0:y1,x0:x1] for q in load_rgba('views/%s/eyes/%s_iris.png'%(v,e))]
    layer=over(wc*0,wc,wa); la=wa.copy()
    layer=np.where(wa[...,None]>0, over(layer,ic,ia*wa), layer)  # source-atop
    out=over(out,layer,la)
    for p in ['lid_0','lash']:
        c,a=[q[y0:y1,x0:x1] for q in load_rgba('views/%s/eyes/%s_%s.png'%(v,e,p))]; out=over(out,c,a)
    return out.round().clip(0,255).astype(np.uint8), base.round().astype(np.uint8), (ia*wa>0.5)
def fill(m): return ndi.binary_fill_holes(m)
def measure(im,e):
    lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(float)
    L=lab[...,0]*100/255; a=lab[...,1]-128; b=lab[...,2]-128
    C=np.hypot(a,b); hue=np.degrees(np.arctan2(b,a))%360
    skin_m=(L>40)&(L<80)&(C>18)&(hue>40)&(hue<80)
    sk=np.median(lab[skin_m],0)
    dE=np.linalg.norm(lab-sk,axis=2)
    dark=L<32
    nons=(dE>16)&~dark
    lb,n=ndi.label(nons)
    best=None
    H,W=L.shape
    for i in range(1,n+1):
        ys,xs=np.nonzero(lb==i)
        if len(xs)<12 or xs.min()==0 or ys.min()==0 or xs.max()==W-1 or ys.max()==H-1: continue
        # opening must be bordered above by dark lash
        top_dark=dark[max(ys.min()-3,0):ys.min()+1, xs.min():xs.max()+1].mean()
        score=len(xs)*(0.2+top_dark)
        if best is None or score>best[0]: best=(score,i)
    op=lb==best[1]
    opf=fill(ndi.binary_closing(op|(dark&ndi.binary_dilation(op,iterations=2)),iterations=1)|op)
    opf=fill(opf)
    if e=='EyeL':
        ir=opf&(hue>95)&(hue<230)&(C>6)&~dark
    else:
        cand=opf&~dark
        Lv=L[cand]; t=np.mean(Lv)
        for _ in range(20):
            lo=Lv[Lv<=t]; hi=Lv[Lv>t]; t2=(lo.mean()+hi.mean())/2
            if abs(t2-t)<0.01: break
            t=t2
        ir=cand&(L<=t)&(C>8)
    ir=fill(ir|(dark&opf))
    li,ni=ndi.label(ir)
    if ni>1:
        sz=ndi.sum(ir,li,range(1,ni+1)); ir=li==(1+int(np.argmax(sz)))
    ys,xs=np.nonzero(ir)
    oy,ox=np.nonzero(opf)
    # lash line: dark pixels near the opening, within a band around it
    band=np.zeros_like(opf); band[max(oy.min()-6,0):oy.max()+4, max(ox.min()-12,0):ox.max()+13]=True
    near=ndi.binary_dilation(opf,iterations=2)
    ld,nd=ndi.label(dark&band)
    keep=np.isin(ld,np.unique(ld[near&(ld>0)]))&(ld>0)
    ly,lx=np.nonzero(keep)
    return dict(iris_centroid=[float(xs.mean()),float(ys.mean())],iris_bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
                iris_w=int(xs.max()-xs.min()+1),iris_px=int(len(xs)),
                opening_bbox=[int(ox.min()),int(oy.min()),int(ox.max()),int(oy.max())],opening_w=int(ox.max()-ox.min()+1),opening_h=int(oy.max()-oy.min()+1),
                lash_bbox=[int(lx.min()),int(ly.min()),int(lx.max()),int(ly.max())],lash_w=int(lx.max()-lx.min()+1),
                skin_lab=[round(float(q),1) for q in sk]), dict(op=opf,ir=ir,lash=keep)
if __name__=='__main__':
    res={}
    for (v,e),(x0,y0,x1,y1) in WIN.items():
        h=AM[v]; f=cv2.imread('reference/apose_turn/frames/f%03d.png'%h['frame'])
        A=np.float32([[h['scale'],0,h['dx']-x0],[0,h['scale'],h['dy']-y0]])
        warp=cv2.warpAffine(f,A,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR)
        live,base,partiris=live_composite(v,e,(x0,y0,x1,y1))
        diff=int((np.abs(live.astype(int)-base.astype(int)).max(2)>2).sum())
        mt,mkt=measure(warp,e); ml,mkl=measure(live,e)
        def sh(m):
            m=json.loads(json.dumps(m))
            for k in ['iris_centroid']: m[k]=[round(m[k][0]+x0,2),round(m[k][1]+y0,2)]
            for k in ['iris_bbox','opening_bbox','lash_bbox']: m[k]=[m[k][0]+x0,m[k][1]+y0,m[k][2]+x0,m[k][3]+y0]
            return m
        mt,ml=sh(mt),sh(ml)
        py,px=np.nonzero(partiris)
        res.setdefault(v,{})[e]=dict(frame='f%03d'%h['frame'],window=[x0,y0,x1,y1],turn=mt,live=ml,
            live_part_iris_centroid=[round(float(px.mean())+x0,2),round(float(py.mean())+y0,2)],live_vs_base_diff_px=diff)
        np.savez(T+'m_%s_%s.npz'%(v,e),warp=warp,live=live,**{'t_'+k:q for k,q in mkt.items()},**{'l_'+k:q for k,q in mkl.items()})
        print(v,e,json.dumps(res[v][e]))
    json.dump(res,open(T+'raw.json','w'),indent=1)
