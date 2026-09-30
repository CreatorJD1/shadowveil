import json,numpy as np,sys
from PIL import Image
sys.path.insert(0,'.'); from handmeas import measure,summarize
R='/workspace/shadowveil/views'
def height(v):
    a=np.array(Image.open(f'{R}/{v}/base.png').convert('RGBA'))[...,3]>0; ys=np.nonzero(a.any(1))[0]; return int(ys.max()-ys.min()+1)
out={}
for v in ['apose','left','right','back']:
    r=json.load(open(f'{R}/{v}/hands/rig.json')); Hh=height(v)
    for s in 'LR':
        palm=[p for p in r['parts'] if p['id']==s+'_palm'][0]
        if not palm.get('file'): continue
        acc=None; pal=None
        for p in r['parts']:
            if p['id'].startswith(s+'_') and p.get('file'):
                a=np.array(Image.open(f'{R}/{v}/hands/{p["file"]}').convert('RGBA'))[...,3]>127
                acc=a if acc is None else acc|a
                if p['id']==s+'_palm': pal=a
        w=(palm['pivotX'],palm['pivotY']); ys,xs=np.nonzero(acc); ax=np.array([xs.mean()-w[0],ys.mean()-w[1]])
        m=measure(acc,w,ax); S=summarize(m)
        # palm part extents along/perp axis
        u=ax/np.linalg.norm(ax); vv=np.array([-u[1],u[0]]); yp,xp=np.nonzero(pal); Pp=np.stack([xp,yp],1)-np.asarray(w,float)
        # middle finger length from its parts
        mid=None
        for k in (1,2,3):
            p=[q for q in r['parts'] if q['id']==f'{s}_Middle{k}'][0]; a=np.array(Image.open(f'{R}/{v}/hands/{p["file"]}').convert('RGBA'))[...,3]>127; mid=a if mid is None else mid|a
        ym,xm=np.nonzero(mid); Pm=np.stack([xm,ym],1)-np.asarray(w,float)
        rec=dict(H=Hh,alg=S,palm_part_len=float((Pp@u).max()),palm_part_width=float(np.ptp(Pp@vv)),middle_parts_len=float(np.ptp(Pm@u)),hand_len=float((np.stack([xs,ys],1)-np.asarray(w,float))@u).max() if False else float(((np.stack([xs,ys],1)-np.asarray(w,float))@u).max()))
        out[f'{v}_{s}']=rec
        print(v,s,'H',Hh,{k:(round(x,1) if isinstance(x,float) else x) for k,x in rec['alg'].items()},'palm part len/wid',round(rec['palm_part_len'],1),round(rec['palm_part_width'],1),'middle parts len',round(rec['middle_parts_len'],1),'hand len',round(rec['hand_len'],1))
json.dump(out,open('ours.json','w'),default=float)
