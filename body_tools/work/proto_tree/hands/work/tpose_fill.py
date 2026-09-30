"""tpose: fill background holes seen through the curled fist with flat skin inside Ring1's frames. A fill pixel is kept
only if, at every curl that frame shows and in every pose, it lands inside the hand's filled silhouette (never outside)."""
import json,numpy as np
from PIL import Image
from scipy import ndimage as ndi
import rigrender2 as R2
d='/workspace/shadowveil/hands/work/frames/tpose_v2'; rig=json.load(open(d+'/rig.json')); by={p['id']:p for p in rig['parts']}
blank='../../hands/work/_blank.png'
for side in 'LR':
    S=np.array(rig['hands'][side]['skinRGB'])
    for fi,cs in [(1,[0.25,0.37,0.5,0.62,0.74]),(2,[0.75,0.87,1.0])]:
        pid=f'{side}_Ring1'; e=by[pid]['frames'][fi]; fp=f"{d}/{e['file']}"; fr=np.array(Image.open(fp).convert('RGBA'))
        cand=np.zeros(fr.shape[:2],bool); states=[]
        for pose in ['Fist','Point','Peace']:
            for c in cs:
                v={k:(x*c if k.startswith('Hand'+side) else 0) for k,x in R2.preset(pose).items()}
                im,_,M,PV,CP=R2.render('tpose',v,d,base=blank); a=np.array(im)[...,3]>100
                env=ndi.binary_fill_holes(a); h=ndi.binary_dilation(env&~a,iterations=1)&env
                states.append((M[pid],env))
                ys,xs=np.nonzero(h)
                if len(xs):
                    q=np.linalg.inv(M[pid])@np.stack([xs,ys,np.ones_like(xs)])
                    cand[np.clip(np.round(q[1]).astype(int),0,1738),np.clip(np.round(q[0]).astype(int),0,1364)]=True
        cand=ndi.binary_closing(cand,iterations=1)&(fr[...,3]<255)
        ys,xs=np.nonzero(cand); ok=np.ones(len(xs),bool)
        for Mx,env in states:
            w=Mx@np.stack([xs,ys,np.ones_like(xs)]); wx=np.clip(np.round(w[0]).astype(int),0,1364); wy=np.clip(np.round(w[1]).astype(int),0,1738)
            ok&=env[wy,wx]
        fr[ys[ok],xs[ok],:3]=S; fr[ys[ok],xs[ok],3]=255; Image.fromarray(fr).save(fp); print(side,fi,'filled',int(ok.sum()),'of',len(xs))
