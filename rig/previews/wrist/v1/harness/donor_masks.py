# donor clip masks: the union of a view's hand parts minus the rim of background skin (e.g. thigh) cut outside her outline.
# Only removes pixels (alpha mask, used with destination-in); never paints. Rim = reachable from transparency through non-line pixels within 8 px.
import json,numpy as np
from PIL import Image
from scipy import ndimage as nd
V='/workspace/shadowveil/views';O='/workspace/shadowveil/rig/previews/wrist/v1/donor_masks'
for v in ['apose','tpose','left','right','back']:
    j=json.load(open(f'{V}/{v}/hands/rig.json'))
    for H in 'LR':
        ps=sorted([p for p in j['parts'] if p.get('file') and not p.get('hidden') and p['id'].startswith(H+'_')],key=lambda p:p['layer'])
        if not ps: continue
        c=Image.new('RGBA',(1365,1739))
        for p in ps: c.alpha_composite(Image.open(f'{V}/{v}/hands/'+p['file']).convert('RGBA'))
        a=np.array(c).astype(np.int32);al=a[...,3];lum=(a[...,0]*299+a[...,1]*587+a[...,2]*114)//1000
        line=nd.binary_dilation((al>64)&(lum<110));tr=al==0;near=nd.distance_transform_edt(~tr)<=6
        free=(~line)&near&(al>0)
        lab,n=nd.label(free|tr);seed=set(np.unique(lab[tr]))-{0};outside=np.isin(lab,list(seed))&(al>0)
        m=(al>0)&~outside;out=np.zeros(a.shape,np.uint8);out[...,3]=np.where(m,255,0);Image.fromarray(out).save(f'{O}/{v}_{H}.png')
        print(v,H,'hand px',int((al>0).sum()),'rim removed',int(outside.sum()))
