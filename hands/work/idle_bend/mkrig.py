# scratch hands rig.json with seg1 pivots moved along the dorsal normal: mkrig.py <view> <out.json> Part=d ...  (d px; negative = palmar)
import json,sys,numpy as np
view,out=sys.argv[1],sys.argv[2];sh=dict((a.split('=')[0],float(a.split('=')[1])) for a in sys.argv[3:])
src=f'/workspace/shadowveil/hands/work/idle_bend/data_backup/{view}_rig.json'
j=json.load(open(src));by={p['id']:p for p in j['parts']};log=[]
for pid,d in sh.items():
    p=by[pid];kid=next(q for q in j['parts'] if q.get('parent')==pid)
    piv=np.array([p['pivotX'],p['pivotY']]);ax=np.array([kid['pivotX'],kid['pivotY']])-piv;ax/=np.linalg.norm(ax)
    n=np.array([ax[1],-ax[0]]);n=n if n[1]<0 else -n
    new=piv+n*d;old=(p['pivotX'],p['pivotY']);p['pivotX'],p['pivotY']=round(float(new[0]),2),round(float(new[1]),2)
    for sk,sv in (j.get('spread') or {}).items():   # keep the spread notes in sync where they pointed at this part's pivot
        for f,e in (sv.get('fingers') or {}).items():
            if e.get('part')==pid and abs(e['pivotX']-old[0])<0.05 and abs(e['pivotY']-old[1])<0.05: e['pivotX'],e['pivotY']=p['pivotX'],p['pivotY']
    log.append(f'{pid}: pivot {old} -> {(p["pivotX"],p["pivotY"])} ({d:+.1f} px dorsal)')
json.dump(j,open(out,'w'),indent=1);print('\n'.join(log))
