# Direction-only sway caps for diagonals_v4 045/315: greedy - at the worst state over the full sweep (view AND frame scale together),
# lower (by 5% of the original limit) the cap of the swaying segment/direction that is driven there with the largest current |deg|; repeat until 0 px
# over the eye opening and the mouth at both scales. Writes degAtPlus1 / degAtMinus1 into both rig.json (view + frame_scale). Never edits pixels.
import json,sys
from sway_gate import *
out={}
for ang in ('045','315'):
    S={}
    for scale in ('view','frame'):
        d,rig,parts,im=load(ang,scale); op,mt=masks(ang,scale); S[scale]=dict(d=d,rig=rig,parts=parts,im=im,tg={'eye_opening':np.nonzero(op)}|{k:np.nonzero(v) for k,v in mt.items()})
    orig={p['id']:(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0) for p in S['view']['parts']}
    cap={i:{'+':v,'-':-v} for i,v in orig.items() if v}
    log=[]
    def apply():
        for sc in S.values():
            for p in sc['parts']:
                if p['id'] in cap: p['degAtPlus1']=round(cap[p['id']]['+'],3); p['degAtMinus1']=round(cap[p['id']]['-'],3)
    for it in range(80):
        apply(); bad=None
        for scale,sc in S.items():
            worst,per=sweep(sc['parts'],sc['im'],sc['rig'].get('swayYMaxPx',3),sc['tg'])
            for k,(n,st) in worst.items():
                if n and (bad is None or n>bad[0]): bad=(n,k,scale,st)
        if bad is None: break
        n,k,scale,st=bad
        xs=st['x'] if 'x' in st else {i:st['X'] for i in cap}
        # segments driven at the worst state that rotate the overlapping chain: pick largest |current cap| in their driven direction
        cand=[(abs(cap[i]['+' if x>0 else '-']),i,'+' if x>0 else '-') for i,x in xs.items() if i in cap and x!=0 and abs(cap[i]['+' if x>0 else '-'])>1e-9]
        by={p['id']:p for p in S['view']['parts']}
        def chain_of(pid):
            c=[pid]
            while by[c[-1]].get('parent') in by: c.append(by[c[-1]]['parent'])
            return c
        rel=set(sum((chain_of(p) for p in st['parts']),[]))
        cand=[c for c in cand if c[1] in rel]
        if not cand: log.append(dict(it=it,stuck=bad)); break
        _,i,dr=max(cand); step=0.05*orig[i]
        cap[i][dr]=(max(0,cap[i][dr]-step) if dr=='+' else min(0,cap[i][dr]+step))
        log.append(dict(it=it,px=n,target=k,scale=scale,state=st,lowered=f'{i} {dr}',to=round(cap[i][dr],3)))
        print(ang,log[-1],flush=True)
    apply(); fin={}
    for scale,sc in S.items():
        worst,per=sweep(sc['parts'],sc['im'],sc['rig'].get('swayYMaxPx',3),sc['tg'])
        fin[scale]={k:dict(px=v[0],state=v[1]) for k,v in worst.items()}
        for p in sc['rig']['parts']:
            q=next(x for x in sc['parts'] if x['id']==p['id'])
            if 'degAtPlus1' in q: p['degAtPlus1']=q['degAtPlus1']; p['degAtMinus1']=q['degAtMinus1']; p['swayCapNote']='direction-only cap (diagonals_v4 sway gate: eye opening + mouth); page needs degAtPlus1/degAtMinus1 support for hair'
        json.dump(sc['rig'],open(f"{sc['d']}/rig.json",'w'),indent=1)
    out[ang]=dict(original_limit_deg=orig,caps={i:dict(degAtPlus1=round(c['+'],3),degAtMinus1=round(c['-'],3)) for i,c in cap.items()},final=fin,iterations=len(log),log=log)
    print(ang,'FINAL',json.dumps(out[ang]['caps']),json.dumps(fin),flush=True)
json.dump(out,open(f'{O}/sway_caps.json','w'),indent=1)
