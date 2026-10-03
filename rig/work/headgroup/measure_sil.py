# silhouette (alpha) shift: head group region (y < neck line) and torso band, frame vs live; IoU-maximising integer shift.
import json,numpy as np; from PIL import Image
D='/workspace/shadowveil/rig/work/qa_post6d5b239/driver_turn'
A_=lambda f:np.array(Image.open(f).convert('RGBA'))[...,3]>=128
def best(F,L,y0,y1,R=32):
    l=L[y0:y1]; res=(-1,0,0)
    for dy in range(-R,R+1):
        f=F[y0+dy:y1+dy]
        for dx in range(-R,R+1):
            fs=np.roll(f,-dx,1); i=(fs&l).sum(); u=(fs|l).sum(); s=i/u
            if s>res[0]: res=(s,dx,dy)
    return res
HO={'apose':1,'left':62,'back':109,'right':160}; out={}
for v,fr in HO.items():
    F=A_(f'{D}/handoff_{v}_frame.png'); L=A_(f'{D}/handoff_{v}_live.png')
    ys=np.nonzero(L.any(1))[0]; top=ys.min()
    r={'frame':fr,'live_top':int(top)}
    s,dx,dy=best(F,L,top,330); r['head_sil']=dict(dx=dx,dy=dy,iou=round(float(s),3))
    s,dx,dy=best(F,L,390,600); r['torso_sil']=dict(dx=dx,dy=dy,iou=round(float(s),3))
    r['head_rel_torso']=dict(dx=r['head_sil']['dx']-r['torso_sil']['dx'],dy=r['head_sil']['dy']-r['torso_sil']['dy'])
    out[v]=r; print(v,r)
json.dump(out,open('handoff_offsets_sil.json','w'),indent=1)
