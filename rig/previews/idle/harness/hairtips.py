# per-tip chained angle (ancestors + own) vs the tip's own limit, from the harness meta hair drives and the view's hair rig.json (read-only)
import json,sys,os
def tips(meta_path):
    m=json.load(open(meta_path));view=m['view']
    j=json.load(open(f'/workspace/shadowveil/views/{view}/hair/rig.json'));ps=j['parts'] if isinstance(j,dict) else j;by={p['id']:p for p in ps}
    wd=lambda p:(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)
    res={}
    for p in ps:
        if not p.get('parent') or p['parent'] not in by or wd(by[p['parent']])==0 or wd(p)==0: continue
        lim=abs(wd(p));mx=0;at=None;own=0
        for f in m['frames']:
            h=f['hair'];tot=0;q=p;n=0
            while q and n<20:
                if q['id'] in h: tot+=wd(q)*h[q['id']][0]
                q=by.get(q.get('parent'));n+=1
            if abs(tot)>abs(mx): mx=tot;at=f['t']
        res[p['id']]=dict(limitDeg=round(lim,2),maxChainDeg=round(abs(mx),2),overDeg=round(max(0,abs(mx)-lim),2),at=at)
    return res
if __name__=='__main__':
    out={}
    for a in sys.argv[2:]:
        n,pth=a.split('=',1);out[n]=tips(pth);print(n,out[n])
    json.dump(out,open(sys.argv[1],'w'),indent=1)
