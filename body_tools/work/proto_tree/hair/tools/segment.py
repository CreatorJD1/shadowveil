# Quality pass: segment long strands into chained root/mid/tip parts with hidden joint caps.
# Input: the pre-quality hair delivery (hair/backup_pre_quality/<view>/), output: views/<view>/hair/.
# Parts stay exact cuts of base.png; the swaying union (= erase mask) is unchanged; caps are copies of the parent's
# fully opaque pixels just above the joint, stored in the child's own image and drawn UNDER the parent (child layer <
# parent layer), so at rest they are covered by identical opaque pixels (0 px rest change, no soft pixel covered twice).
import json, os, sys, shutil, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import disk, dilation
from skimage.graph import MCP_Geometric
R='/workspace/shadowveil'; SRC=R+'/hair/backup_pre_quality/{}'; OUT=R+'/views/{}/hair'
VIEWS=['apose','tpose','left','right','back']
CFG=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'quality_cfg.json')))
LONG=60; CAPDEPTH=6; CFG_MED={}
def FORB(v):
    import glob
    f_=np.zeros((1739,1365),bool)
    for f in glob.glob(f'{R}/views/{v}/eyes/Eye*_*.png')+glob.glob(f'{R}/views/{v}/mouth/*.png'):
        if 'chroma' in f: continue
        f_|=np.array(Image.open(f).convert('RGBA'))[...,3]>0
    return ndi.binary_dilation(f_,iterations=2)
def geodesic(S,seed):
    D=dilation(S,disk(3))  # bridge folded fragments (<=6px apart) so they follow their trunk
    cost=np.where(D,1.0,np.inf); cost[S]=1.0; cost[D&~S]=1.5
    m=MCP_Geometric(cost,fully_connected=True); dist,_=m.find_costs(list(zip(*np.where(seed))))
    bad=S&~np.isfinite(dist)
    if bad.any():  # far fragments: nearest reachable pixel's distance + straight gap
        ok=S&np.isfinite(dist); dt,(iy,ix)=ndi.distance_transform_edt(~ok,return_indices=True)
        dist=np.where(bad,dist[iy,ix]+dt,dist)
    return dist
def seed_of(S,px,py):
    H,W=S.shape; yy,xx=np.mgrid[:H,:W]; d=np.hypot(xx-px,yy-py); d[~S]=1e9
    return S&(d<=max(2.5,d.min()+1))
def pick_split(S,A,geo,t0,lo,hi):
    """choose a threshold near t0 (within [lo,hi]) where the cut runs through fully opaque hair on both sides
    (parent cap band t-CAPDEPTH..t and child band t..t+3), so the hidden cap can back the whole AA edge of the cut"""
    best=None
    for t in np.arange(max(3,lo),hi+0.01,0.5):
        ring=S&(geo>=t-CAPDEPTH)&(geo<t); cring=S&(geo>=t)&(geo<t+3)
        cut=S&(geo>=t)&(geo<t+1.5)
        if not ring.any() or not cut.any(): continue
        opq=min((A[ring]==255).mean(),(A[cring]==255).mean()); w=cut.sum()
        score=opq*10-abs(t-t0)*0.05-0.05*w
        if best is None or score>best[0]: best=(score,t,opq)
    SPLITLOG.append(best)
    return best[1] if best else t0
SPLITLOG=[]
def main(views):
    meta={}
    for v in views:
        src=SRC.format(v); od=OUT.format(v); rig=json.load(open(f'{src}/rig.json')); parts=rig['parts']
        base=np.array(Image.open(f'{R}/views/{v}/base.png').convert('RGBA'))
        H,W=base.shape[:2]; vc=CFG['views'][v]; out=[]; files={}
        for f in os.listdir(od):
            if f.endswith('.png'): os.remove(os.path.join(od,f))
        def cut(mask): o=np.zeros_like(base); o[mask]=base[mask]; return o
        strands=[p for p in parts if p['id'].startswith('strand_')]
        others=[p for p in parts if not p['id'].startswith('strand_')]
        for p in others:
            shutil.copy(f"{src}/{p['file']}",f"{od}/{p['file']}"); q=dict(p); out.append(q)
            if p['id']=='bun': q['swayY']=vc.get('bunSwayY',p['swayY'])
        # hair_back: also fill (median hair colour) the opaque erased pixels that sit INSIDE her silhouette and have
        # nothing under them (base_body transparent there): when a strand root sways off the ear/temple they would
        # otherwise show the background through her head. Hidden at rest by the opaque strand pixel above.
        em=np.array(Image.open(f'{R}/hair/{v}_hair_erase_mask.png'))>127
        bb=np.array(Image.open(f'{R}/views/{v}/base_body.png'))
        hb=np.array(Image.open(f'{od}/hair_back.png'))
        solid=(bb[...,3]>0)|(hb[...,3]>0)
        enc=ndi.binary_fill_holes(ndi.binary_closing(solid,iterations=3))
        hole=em&(base[...,3]==255)&(bb[...,3]==0)&(hb[...,3]==0)&enc&~FORB(v)
        fillc=np.median(hb[(hb[...,3]==255)&(hb[...,:3]!=base[...,:3]).any(-1)][:,:3],axis=0).astype(np.uint8) if ((hb[...,3]==255)&(hb[...,:3]!=base[...,:3]).any(-1)).any() else np.array(CFG_MED[v],np.uint8)
        hb[hole,:3]=fillc; hb[hole,3]=255; Image.fromarray(hb).save(f'{od}/hair_back.png')
        # fixed layers never need to cover a face part: hair_front duplicates opaque base_body pixels and hair_back sits
        # under base_body, so pixels inside the face forbidden region are dropped from both (rest unchanged: base_body
        # still holds those exact opaque pixels). Keeps hair clear of new eye/mouth frames such as lid_7.
        F=FORB(v); hf=np.array(Image.open(f'{od}/hair_front.png'))
        bbop=bb[...,3]==255; dropf=F&(hf[...,3]>0)&bbop
        hf[dropf]=0; Image.fromarray(hf).save(f'{od}/hair_front.png')
        dropb=F&(hb[...,3]>0)&bbop; hb[dropb]=0; Image.fromarray(hb).save(f'{od}/hair_back.png')
        vm=meta[v]={'hair_front_dropped_in_forbidden':int(dropf.sum()),'hair_back_dropped_in_forbidden':int(dropb.sum()),'hair_back_added_fill':int(hole.sum()),'fill_rgb':fillc.tolist()}
        for i,p in enumerate(strands):
            sid=p['id']; sc=vc['strands'].get(sid,{})
            img=np.array(Image.open(f"{src}/{p['file']}")); A=img[...,3]; S=A>0
            geo=geodesic(S,seed_of(S,p['pivotX'],p['pivotY'])); geo[~S]=np.inf
            L=float(np.percentile(geo[S],99.5)); n=sc.get('segments',1 if L<=LONG else (2 if L<=105 else 3))
            k=sc.get('k',1.0); sy=sc.get('swayY',1.0)
            base_layer=601+3*i
            segs=[]  # list of (mask, pivot)
            if n==1:
                segs=[(S,(p['pivotX'],p['pivotY']))]
            else:
                nn=sc.get('split_of',n)   # compute split positions as for nn segments, keep the first n-1
                ts=sc.get('splits') or [pick_split(S,A,geo,L*j/nn,L*j/nn-sc.get('win',14),L*j/nn+sc.get('win',14)) for j in range(1,nn)]
                ts=ts[:n-1]
                rem=S.copy(); prev_piv=(p['pivotX'],p['pivotY']); masks=[]
                for t in ts:
                    far=rem&(geo>=t)
                    lab,kk=ndi.label(dilation(far,disk(3)),structure=np.ones((3,3)))
                    # trunk = biggest component past t (fragments within 6px ride with it); side branches stay with the parent
                    sz=ndi.sum(far,lab,range(1,kk+1)); trunk=(lab==1+int(np.argmax(sz)))&far
                    masks.append(rem&~trunk); rem=trunk
                masks.append(rem)
                pivs=[prev_piv]
                for j in range(1,n):
                    ch=masks[j]; t=geo[ch].min(); ring=ch&(geo<t+1.5)&~np.isin(np.arange(1),[])
                    ys,xs=np.where(ring); pivs.append((float(round(xs.mean()+0.0,1)),float(round(ys.mean(),1))))
                segs=list(zip(masks,pivs))
            names=[sid] if n==1 else ([sid,sid+'_tip'] if n==2 else [sid,sid+'_mid',sid+'_tip'])
            wts=[1.0] if n==1 else ([0.6,1.0] if n==2 else [0.6,0.8,1.0])
            degs=sc.get('deg',[10.0] if n==1 else ([8.5,8.5] if n==2 else [7.0,7.0,7.0]))
            if not isinstance(degs,list): degs=[degs]*n
            sys_=sc.get('swayYs',[sy]*n)
            vm[sid]=dict(L=round(L,1),n=n,segs=[],split_opaque=[(round(x[1],1),round(x[2],2)) for x in SPLITLOG[-(sc.get('split_of',n)-1):]] if n>1 else [])
            for j,((m,(px,py)),nm) in enumerate(zip(segs,names)):
                im=cut(m); capn=0
                if j>0:
                    par=segs[j-1][0]; t=geo[m].min()
                    ring=m&(geo<t+1.5)
                    cap=par&(A==255)&(geo>=t-CAPDEPTH)&(geo<t)&dilation(ring,disk(CAPDEPTH+1))
                    im[cap]=base[cap]; capn=int(cap.sum())
                Image.fromarray(im).save(f'{od}/{nm}.png')
                out.append(dict(id=nm,file=nm+'.png',x=0,y=0,pivotX=float(px),pivotY=float(py),
                    parent=p['parent'] if j==0 else names[j-1],layer=base_layer+(n-1-j) if n>1 else base_layer,
                    swayWeight=round(min(1.0,wts[j]*k),2),maxSwayDeg=float(degs[j]),swayY=round(min(1.0,sys_[j]),3)))
                vm[sid]['segs'].append(dict(id=nm,px=int(m.sum()),cap=capn,pivot=[px,py]))
        json.dump({'swayYMaxPx':rig['swayYMaxPx'],'parts':out},open(f'{od}/rig.json','w'),indent=1)
        print(v,json.dumps(vm))
    return meta
if __name__=='__main__': main(sys.argv[1:] or VIEWS)
