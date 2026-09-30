"""Prototype curl frames <part>_f0..f2.png (apose). f0 = exact delivered part. f1/f2 = flat redraws:
 distal (Finger3, Thumb3): foreshortened along the finger axis about its own pivot (70% / 45%), rounded pad, pad crease.
 Finger1/2, Thumb2: same length (pivots are fixed by contract) but drawn curled: rounded knuckle bulge at the far joint
 + knuckle crease line(s). Flat skin + sampled line colour, 4x supersampled edges."""
import json, numpy as np, sys, os
from PIL import Image
from scipy import ndimage as ndi
ROOT='/workspace/shadowveil'; SS=4
def load(v,f): return np.array(Image.open(f'{ROOT}/views/{v}/hands/{f}').convert('RGBA'))
def make_frames(v,out):
    rig=json.load(open(f'{ROOT}/views/{v}/hands/rig.json')); by={p['id']:p for p in rig['parts']}
    kids={}
    for p in rig['parts']:
        if p.get('parent'): kids[p['parent']]=p['id']
    made={}
    for p in rig['parts']:
        pid=p['id']; side,nm=pid.split('_')
        if nm=='palm' or not p.get('file') or nm=='Thumb1': continue
        H=rig['hands'][side]; S=np.array(H['skinRGB'],float); Lc=np.array(H['lineRGB'],float)
        x0,y0,x1,y1=H['box']; x0-=10;y0-=10;x1+=10;y1+=10
        A=load(v,p['file'])[y0:y1,x0:x1]
        piv=np.array([p['pivotX']-x0,p['pivotY']-y0])
        k=int(nm[-1]); child=kids.get(pid)
        if child: end=np.array([by[child]['pivotX']-x0,by[child]['pivotY']-y0])
        else:
            ys,xs=np.nonzero(A[...,3]>0); pts=np.stack([xs,ys],1).astype(float)
            # tip = farthest visible pixel from pivot
            end=pts[np.argmax(((pts-piv)**2).sum(1))]
        d=end-piv; L=np.linalg.norm(d); d/=L; n=np.array([-d[1],d[0]])
        m=A[...,3]>0
        # half width at the far end
        dtm=ndi.distance_transform_edt(m)
        def r_at(q):
            qi=(int(np.clip(round(q[1]),0,m.shape[0]-1)),int(np.clip(round(q[0]),0,m.shape[1]-1))); return max(float(dtm[qi]),2.0)
        hs,ws=m.shape
        # supersampled coordinates
        Y,X=np.mgrid[0:hs*SS,0:ws*SS]; Px=(X+0.5)/SS-0.5; Py=(Y+0.5)/SS-0.5
        rel=np.stack([Px-piv[0],Py-piv[1]],-1); a=rel@d; b=rel@n
        frames=[None]
        for fi,(scale,bulge) in enumerate([(0.72,1.08),(0.45,1.18)],start=1):
            distal=(child is None)
            s=scale if distal else 1.0
            # inverse-map supersampled pixel into f0 space (stretch along axis)
            srcx=piv[0]+d[0]*(a/s)+n[0]*b; srcy=piv[1]+d[1]*(a/s)+n[1]*b
            M=ndi.map_coordinates(m.astype(float),[srcy,srcx],order=1)>0.5
            re=r_at(piv+d*L*0.85)
            if not distal:
                # rounded knuckle bulge at the far joint
                M|=((Px-end[0])**2+(Py-end[1])**2)<=(re*bulge)**2
            else:
                tipc=piv+d*L*s-d*re*0.9
                M|=(((Px-tipc[0])**2+(Py-tipc[1])**2)<=(re*1.02)**2)&(a>0)
            M&=a>-re*1.2   # keep near-pivot overlap only
            base_side=a<=0.8   # the cut at the own pivot: no outline there (sits on parent)
            dt=ndi.distance_transform_edt(np.pad(M,4))[4:-4,4:-4]/SS
            line=(dt<=1.25)&M&~base_side
            # creases: short arcs across the segment
            cre=np.zeros_like(M)
            spots=[0.8] if not distal else [0.28]
            if fi==2 and not distal: spots=[0.2,0.8]
            for t in spots:
                at=L*s*t
                c=np.abs(a-at-0.15*(b**2)/max(re,1))<=0.55
                cre|=c&(np.abs(b)<=re*0.55)&M
            col=np.zeros(M.shape+(4,)); col[...,:3]=S; col[...,3]=M*255.0
            col[line|cre,:3]=Lc
            # downsample (premultiplied)
            pm=col.copy(); pm[...,:3]*=pm[...,3:]/255
            ds=pm.reshape(hs,SS,ws,SS,4).mean((1,3))
            al=ds[...,3:]; rgb=np.where(al>0,ds[...,:3]/np.maximum(al,1e-6)*255,0)
            fr=np.zeros((1739,1365,4),np.uint8)
            fr[y0:y1,x0:x1,:3]=np.clip(np.round(rgb),0,255); fr[y0:y1,x0:x1,3]=np.clip(np.round(al[...,0]),0,255)
            frames.append(fr)
        full0=load(v,p['file'])
        Image.fromarray(full0).save(f'{out}/{pid}_f0.png')
        for fi in (1,2): Image.fromarray(frames[fi]).save(f'{out}/{pid}_f{fi}.png')
        made[pid]=[f'{pid}_f{i}.png' for i in range(3)]
    # parts without curl frames (palm, Thumb1): f0=f1=f2 copies so every entry has 3 frames
    for p in rig['parts']:
        if p.get('file') and p['id'] not in made:
            im=load(v,p['file'])
            for i in range(3): Image.fromarray(im).save(f"{out}/{p['id']}_f{i}.png")
            made[p['id']]=[f"{p['id']}_f{i}.png" for i in range(3)]
    json.dump({'view':v,'frameSelect':'frame = round(curl*2) -> f0 (curl<0.25), f1 (0.25-0.75), f2 (>0.75); same canvas and pivot as the part','frames':made},open(f'{out}/frames.json','w'),indent=1)
    return made
if __name__=='__main__':
    v=sys.argv[1] if len(sys.argv)>1 else 'apose'
    out=f'{ROOT}/hands/work/frames/{v}'; os.makedirs(out,exist_ok=True); make_frames(v,out); print('ok',v)
