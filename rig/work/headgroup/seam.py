# head group check + neck seam: with the offset, does head/face/hair move by exactly (dx,dy)? gap/overlap px in the neck band.
import json,numpy as np; from PIL import Image
L=lambda f:np.array(Image.open(f).convert('RGBA')).astype(int)
H=json.load(open('hg_render.json')); out={}
NECK={'apose':(600,300,765,400),'left':(590,290,740,400),'right':(625,290,775,400),'back':(600,280,760,400)}
FACE={'apose':(610,160,755,300),'left':(585,170,690,300),'right':(675,170,780,300),'back':(610,120,750,260)}
for v,info in H.items():
    dx,dy=info['applied']['dx'],info['applied']['dy']
    for mode in ('a','r'):
        A0=L(f'renders/{v}_{mode}0.png'); A1=L(f'renders/{v}_{mode}1.png'); base=L(f'/workspace/shadowveil/views/{v}/base.png')
        x0,y0,x1,y1=FACE[v]; f0=A0[y0:y1,x0:x1]; f1=A1[y0+dy:y1+dy,x0+dx:x1+dx]; face_exact=int((np.abs(f0-f1).max(-1)>0).sum())
        x0,y0,x1,y1=NECK[v]; n0=A0[y0:y1,x0:x1]; n1=A1[y0:y1,x0:x1]
        op0=n0[...,3]>=128; op1=n1[...,3]>=128
        gap=int((op0&~op1).sum())                       # was skin/body, now see-through
        newcov=int((~op0&op1).sum())                    # new opaque px outside her neck silhouette
        changed=int((np.abs(n0-n1).max(-1)>8).sum())
        # neck stretch/overlap: rows in the band where the head-moved content differs (head over collar = overlap when dy>0)
        rows=np.nonzero((np.abs(n0-n1).max(-1)>8).any(1))[0]
        r=dict(offset=[dx,dy],face_px_not_moved_exactly=face_exact,a0_vs_base_px=int((np.abs(A0-base).max(-1)>0).sum()),
               neck_gap_px=gap,neck_new_coverage_px=newcov,neck_band_changed_px=changed,neck_rows_changed=[int(rows.min()+y0),int(rows.max()+y0)] if len(rows) else None)
        out[f'{v}:{"posed" if mode=="a" else "rest"}']=r; print(v,mode,r)
json.dump(out,open('seam.json','w'),indent=1)
