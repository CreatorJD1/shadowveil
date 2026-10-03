"""v2 'greedy': start from 'partial' (F5 fill only on px that already carry her AA alpha), then re-add F5's fully-new skin px
(closest to her live silhouette first) as long as the Ring1 median chord AND max width stay <= LIMIT px over the live f1."""
import sys,os,shutil,json,numpy as np
sys.path.insert(0,'/workspace/shadowveil/hands/qa/scale_audit/tools')
from PIL import Image
from scipy import ndimage as nd
import f5_meas
R='/workspace/shadowveil/'; ST=R+'hands/staged/f5_lineart/back/'; LV=R+'views/back/hands/'
LIMIT=float(sys.argv[1]); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
for f in os.listdir(ST):
    if f.endswith('.png') or f=='rig.json': shutil.copy(ST+f,out+'/'+f)
rig=json.load(open(LV+'rig.json')); P={p['id']:p for p in rig['parts']}; log={}
def medw(a,piv):
    tmp=out+'/_t.png'; Image.fromarray(a).save(tmp); g,_=f5_meas.geo(tmp,piv); os.remove(tmp); return np.array([g['median_chord_w'],g['width'],g['reach']])
for pid in ('L_Ring1','R_Ring1'):
    piv=(P[pid]['pivotX'],P[pid]['pivotY'])
    l=np.array(Image.open(LV+pid+'_f1.png').convert('RGBA')); s=np.array(Image.open(ST+pid+'_f1.png').convert('RGBA'))
    ch=(l!=s).any(2); base=ch&(l[...,3]>0); v=l.copy(); v[base]=s[base]; w0=medw(l,piv)
    cand=ch&~base; dist=nd.distance_transform_edt(~(v[...,3]>=128)); order=sorted(zip(*np.nonzero(cand)),key=lambda p:dist[p])
    added=[]
    for (y,x) in order:
        t=v.copy(); t[y,x]=s[y,x]
        dd=medw(t,piv)-w0
        if dd[0]<=LIMIT and dd[1]<=LIMIT and abs(dd[2])<=1e-6: v=t; added.append([int(x),int(y)])
    Image.fromarray(v).save(out+f'/{pid}_f1.png')
    log[pid]=dict(f5_changed=int(ch.sum()),kept_partial=int(base.sum()),readded_new=len(added),dropped=int(cand.sum())-len(added),d_medchord_maxw_reach=[round(float(x),3) for x in medw(v,piv)-w0],readded_px=added)
    print(pid,{k:x for k,x in log[pid].items() if k!='readded_px'})
json.dump(log,open(out+'/v2_log.json','w'))
