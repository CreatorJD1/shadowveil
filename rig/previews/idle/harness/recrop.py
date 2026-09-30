# re-pick the worst frame per run by defect pixels only (body holes+tears+seam, then hands, then hair); interiorLost is limb displacement, not a defect
import json,sys,os,glob
import numpy as np
from PIL import Image
from scipy import ndimage as nd
IDLE='/workspace/shadowveil/rig/previews/idle'
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1]; return x*x+y*y<=r*r
def enclosed(op):
    lab,n=nd.label(~op); border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));keep=np.ones(n+1,bool);keep[list(border)]=False;keep[0]=False;return keep[lab]
def masks(A):
    op=A>=128;enc=enclosed(op);cl=nd.binary_closing(op,structure=disk(3),border_value=0);return enc,cl&~op&~enc,nd.binary_erosion(op,structure=disk(4),border_value=0)&(A<255)
for qp in sys.argv[1:]:
    q=json.load(open(qp));s=q['summary'];name=s['name'];qadir=os.path.dirname(qp);W_=os.environ.get('WORK',IDLE+'/work')+'/'+name;view=s['view']
    sc=lambda r:(r['holesBy']['body']+r['tearsBy']['body']+r['seamBy']['body'],r['holesBy']['hands']+r['tearsBy']['hands']+r['seamBy']['hands'],r['newHoles']+r['newTears']+r['newSeamAlpha'])
    w=max(q['frames'],key=sc)
    for f in glob.glob(f'{qadir}/{name}_worst_*'): os.remove(f)
    RA=np.array(Image.open(W_+'/rest.png'))[...,3];im=Image.open(f"{W_}/frames/f{w['frame']:04d}.png");A=np.array(im)[...,3]
    re,rt,rs=masks(RA);e,t,se=masks(A)
    d=lambda m,r:nd.binary_dilation(m,structure=disk(r))
    bad_all=(e&~d(re,3))|(t&~d(rt,3))|(se&~d(rs,2))
    # owner regions (same as qa.py)
    VD=f'/workspace/shadowveil/views/{view}'
    def union(o):
        try: j=json.load(open(f'{VD}/{o}/rig.json'))
        except Exception: return np.zeros(RA.shape,bool)
        m=np.zeros(RA.shape,bool)
        for p in (j if isinstance(j,list) else j.get('parts',[])):
            fn=p.get('file') if isinstance(p,dict) else None
            if fn and os.path.exists(f'{VD}/{o}/{fn}'):
                a=np.array(Image.open(f'{VD}/{o}/{fn}').convert('RGBA'))[...,3]
                if a.shape==RA.shape: m|=a>0
        return m
    HAIR=d(union('hair'),45);HANDS=d(union('hands'),12)&~HAIR;BODY=~HAIR&~HANDS
    kind='body'
    bad=bad_all&BODY
    if sc(w)[0]==0 or not bad.any(): bad=bad_all&HANDS;kind='hands'
    if not bad.any(): bad=bad_all;kind='any'
    if bad.any():
        lab,n=nd.label(d(bad,8));cnt=nd.sum(bad,lab,range(1,n+1));big=int(np.argmax(cnt))+1;yy,xx=np.nonzero(bad&(lab==big))
        cx,cy=(xx.min()+xx.max())//2,(yy.min()+yy.max())//2;hw=max(90,(xx.max()-xx.min())//2+60);hh=max(90,(yy.max()-yy.min())//2+60)
        box=[int(max(0,cx-hw)),int(max(0,cy-hh)),int(min(RA.shape[1],cx+hw)),int(min(RA.shape[0],cy+hh))];bb=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]
    else: box=[0,0,RA.shape[1],RA.shape[0]];bb=None
    def comp(img):
        g=Image.new('RGBA',img.size,(128,128,128,255));g.alpha_composite(img);return g.convert('RGB').crop(box)
    k=3 if box[2]-box[0]<300 else 2
    base=f"{qadir}/{name}_worst_f{w['frame']:04d}_t{w['t']:.3f}s"
    c=comp(im);c.resize((c.width*k,c.height*k),Image.NEAREST).save(base+'.png')
    r=comp(Image.open(W_+'/rest.png'));r.resize((r.width*k,r.height*k),Image.NEAREST).save(base+'_REST_same_crop.png')
    mk=Image.fromarray((bad_all[box[1]:box[3],box[0]:box[2]]*255).astype(np.uint8));mk.resize((mk.width*k,mk.height*k),Image.NEAREST).save(base+'_defect_mask.png')
    s['worst']=dict(frame=w['frame'],t=w['t'],kind=kind,body=dict(holes=w['holesBy']['body'],tears=w['tearsBy']['body'],seam=w['seamBy']['body']),hands=dict(holes=w['holesBy']['hands'],tears=w['tearsBy']['hands'],seam=w['seamBy']['hands']),
        hair=dict(holes=w['holesBy']['hair'],tears=w['tearsBy']['hair'],seam=w['seamBy']['hair']),tearsAtJoints=w['tearsAtJoints'],clusterBBox=bb,cropBox=box,crop=base+'.png',restCrop=base+'_REST_same_crop.png',mask=base+'_defect_mask.png')
    json.dump(q,open(qp,'w'),indent=1)
    print(name,'f%d t=%.3f'%(w['frame'],w['t']),kind,s['worst']['body'],s['worst']['hands'],bb,os.path.basename(base+'.png'))
