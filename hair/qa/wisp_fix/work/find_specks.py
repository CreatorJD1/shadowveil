# Proposal only (Task 2 on hold): strand-coloured specks in views/<v>/base_body.png that lie just outside the strands and the
# hair erase mask. READ-ONLY on views/ and hair/*_hair_erase_mask.png; writes only to hair/qa/wisp_fix/erase_mask_proposal/.
# A candidate pixel: base_body alpha>0, not in the erase mask, not in any hair part, within 2 px of a swaying strand, strand-coloured
# (bluish navy/black like the strand's own pixels: b>=r+15 and max(r,g,b)<=110), and either
#  (A) in a small isolated opaque component of base_body (<=20 px, or <=300 px lying entirely within 2 px of the strands), or
#  (B) enclosed by the strand (>=4 of its 8 neighbours are strand pixels).
import numpy as np, json, sys
from PIL import Image
from scipy import ndimage as ndi
R='/workspace/shadowveil'; OUT=R+'/hair/qa/wisp_fix/erase_mask_proposal'
def A(p): return np.array(Image.open(p).convert('RGBA')).astype(int)
res={}
for v in ['apose','tpose','left','right','back']:
    hd=f'{R}/views/{v}/hair'; J=json.load(open(hd+'/rig.json')); rig=J['parts']
    bb=A(f'{R}/views/{v}/base_body.png'); H,W=bb.shape[:2]
    em=np.array(Image.open(f'{R}/hair/{v}_hair_erase_mask.png').convert('L'))>127
    parts={e['id']:A(hd+'/'+e['file'])[...,3]>0 for e in rig}
    anyhair=np.any(list(parts.values()),0)
    r,g,b=bb[...,0],bb[...,1],bb[...,2]
    col=(b>=r+15)&(np.maximum(np.maximum(r,g),b)<=110)
    cand=(bb[...,3]>0)&~em&~anyhair&col
    body=(bb[...,3]>0)&~em
    lab,n=ndi.label(body,structure=np.ones((3,3)))
    sizes=ndi.sum(np.ones_like(lab),lab,index=np.arange(n+1)); small=(sizes[lab]<=20)&(lab>0)
    # also: any component (<=300 px) that lies entirely within 2 px of the swaying strands (a chain of edge specks along a strand)
    swu=np.any([parts[e['id']] for e in rig if e['swayWeight']>0 and e['id']!='bun'],0)
    nearu=ndi.binary_dilation(swu,iterations=2)
    outside=ndi.sum((~nearu).astype(int),lab,index=np.arange(n+1))
    small|=((outside[lab]==0)&(sizes[lab]<=300)&(lab>0))
    prop=np.zeros((H,W),bool); per={}; pix={}
    sw=[e for e in rig if e['swayWeight']>0 and e['id']!='bun']   # bun: moves <=0.45 px (QA), reported separately, not proposed
    D=np.stack([ndi.distance_transform_edt(~parts[e['id']]) for e in sw])
    NB=np.stack([ndi.convolve(parts[e['id']].astype(int),np.array([[1,1,1],[1,0,1],[1,1,1]]),mode='constant') for e in sw])
    own=np.argmin(D,0); dmin=D.min(0); nbown=np.take_along_axis(NB,own[None],0)[0]
    c=cand&(dmin<=2)&(small|(nbown>=4))
    for k,e in enumerate(sw):      # each speck px goes to its NEAREST strand
        ck=c&(own==k)
        if ck.sum():
            per[e['id']]=dict(px=int(ck.sum()),isolated=int((ck&small).sum()),enclosed=int((ck&~small).sum()))
            ys,xs=np.nonzero(ck); pix[e['id']]=[[int(x),int(y)] for x,y in zip(xs,ys)]
    prop=c
    res[v]=dict(total=int(prop.sum()),per_strand=per,pixels_xy=pix)
    Image.fromarray((prop*255).astype(np.uint8)).save(f'{OUT}/{v}_hair_erase_mask_ADD.png')
    Image.fromarray(((em|prop)*255).astype(np.uint8)).save(f'{OUT}/{v}_hair_erase_mask_PROPOSED.png')
    print(v,prop.sum(),per,flush=True)
json.dump(res,open(f'{OUT}/proposal.json','w'),indent=1)
