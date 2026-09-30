import json,numpy as np,sys
from PIL import Image
sys.path.insert(0,'.'); from shape import shape_metrics
R='/workspace/shadowveil/views'; out={}
for v in ['apose','left','right','back']:
    r=json.load(open(f'{R}/{v}/hands/rig.json')); a0=np.array(Image.open(f'{R}/{v}/base.png').convert('RGBA'))[...,3]>0; ys=np.nonzero(a0.any(1))[0]; Hh=int(ys.max()-ys.min()+1)
    for s in 'LR':
        P={p['id']:p for p in r['parts']}
        if not P[s+'_palm'].get('file'): continue
        acc=None
        for p in r['parts']:
            if p['id'].startswith(s+'_') and p.get('file'):
                a=np.array(Image.open(f'{R}/{v}/hands/{p["file"]}').convert('RGBA'))[...,3]>127; acc=a if acc is None else acc|a
        w=np.array([P[s+'_palm']['pivotX'],P[s+'_palm']['pivotY']]); mcp=np.array([P[s+'_Middle1']['pivotX'],P[s+'_Middle1']['pivotY']])
        ax=mcp-w; M=shape_metrics(acc,w,ax)
        idx=np.array([P[s+'_Index1']['pivotX'],P[s+'_Index1']['pivotY']]); pk=np.array([P[s+'_Pinky1']['pivotX'],P[s+'_Pinky1']['pivotY']])
        m3=np.array(Image.open(f'{R}/{v}/hands/{P[s+"_Middle3"]["file"]}').convert('RGBA'))[...,3]>127; y3,x3=np.nonzero(m3); u=ax/np.linalg.norm(ax)
        tipd=float(((np.stack([x3,y3],1)-mcp)@u).max())
        rec=dict(H=Hh,palm_len=float(np.linalg.norm(mcp-w)),palm_w=float(np.linalg.norm(idx-pk)),middle_len=tipd,**{k:M[k] for k in ('L','W','thumb_side','bulge_diff','tips')})
        rec.update({k+'_n':rec[k]/Hh for k in ('palm_len','palm_w','middle_len','L','W')}); out[f'{v}_{s}']=rec
        print(v,s,{k:(round(x,4) if isinstance(x,float) else x) for k,x in rec.items()})
json.dump(out,open('ours.json','w'))
