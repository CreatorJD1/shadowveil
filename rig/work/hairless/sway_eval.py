import json,numpy as np; from PIL import Image; from scipy import ndimage as nd
L=lambda f:np.array(Image.open(f).convert('RGBA')).astype(int)
base=L('/workspace/shadowveil/views/apose/base.png'); H0=L('hairless_rest.png')
head=np.zeros(base.shape[:2],bool); head[:430]=True
inside=base[...,3]>=250                    # her silhouette at rest
def holes(a):
    t=a<250; lab,n=nd.label(t); b=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]])); return np.isin(lab,[i for i in range(1,n+1) if i not in b])
ear=np.zeros_like(head); ear[224:229,752:755]=True
out={'rest':dict(diff_vs_base_px=int((np.abs(H0-base).max(-1)>0).sum()),ear_6px_changed=int((np.abs(H0-base).max(-1)>0)[ear].sum()))}
for t in ['sx+1','sx-1','sy+1','sy-1','sx+1sy+1','sx-1sy+1','sx+1sy-1','sx-1sy-1']:
    for tag in ('hairless','live'):
        A=L(f'{tag}_{t}.png'); op=A[...,3]>=250
        white=(A[...,3]>=128)&(A[...,:3].min(-1)>=215)
        blue=(A[...,3]>=128)&(A[...,2]>A[...,0]+30)&(A[...,2]>120)
        r=dict(background_inside_rest_silhouette_px=int((inside&~op&head).sum()),enclosed_see_through_px=int((holes(A[...,3])&head).sum()),
               white_px=int((white&head).sum()),blue_px=int((blue&head).sum()))
        out.setdefault(t,{})[tag]=r
    h,l=out[t]['hairless'],out[t]['live']; out[t]['new_in_hairless']={k:h[k]-l[k] for k in h}
    print(t,out[t])
json.dump(out,open('sway_eval.json','w'),indent=1); print(out['rest'])
