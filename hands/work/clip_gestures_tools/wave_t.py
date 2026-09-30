import sys,numpy as np
sys.path.insert(0,'/workspace/gb'); from tracks import track; from fingers import analyse
c=sys.argv[1]; side=sys.argv[2]; a,b=int(sys.argv[3]),int(sys.argv[4])
tr,F=track(c); t=tr[side]; rows=[]
for i in range(a,b):
    r=analyse(F[i],t['x'][i],t['y'][i],None)
    cs=[q for q in r['comps'] if q['len']>25]
    angs=[q['ang'] for q in cs]
    rows.append((i,len(cs),round(float(np.mean(angs)),1) if angs else None,round(max(angs)-min(angs),1) if len(angs)>1 else None,[round(q['ang']) for q in cs]))
for r in rows: print(*r)
