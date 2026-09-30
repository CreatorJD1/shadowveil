import json,sys,numpy as np
def summ(name, verbose=True):
    d=json.load(open(name+'.check.json'));R=d['rows'];v=d['view']
    def top(key,k=3): return sorted(((r[key],r['f']) for r in R),reverse=True)[:k]
    fl=[(max(abs(r['foot'][s]['dy_target']) for s in r['foot'] if r['foot'][s]),r['f']) for r in R]
    fdx=[(max(abs(r['foot'][s]['dx']) for s in r['foot'] if r['foot'][s]),r['f']) for r in R]
    ha=[r['f'] for r in R if r['headAxis']]
    ns=np.array([r['neckSharp'] for r in R]);
    tog=[i for i in range(1,len(R)) if R[i]['headAxis']!=R[i-1]['headAxis']]
    jump=[(i,round(float(ns[i]-ns[i-1]),4)) for i in tog]
    other=np.abs(np.diff(ns)); other_max=float(np.max([other[i-1] for i in range(1,len(R)) if i not in tog])) if len(R)>1 else 0
    s={'name':name,'holes_body_max':top('holes_body'),'holes_body_frames':sum(r['holes_body']>0 for r in R),
       'worst_hole_comp':max(((r['holes_body_comps'][0],r['f']) for r in R if r['holes_body_comps']),default=None),
       'tears_body_max':top('tears_body'),'tears_body_frames':sum(r['tears_body']>0 for r in R),'worst_tear_comp':max(((r['tears_body_comps'][0],r['f']) for r in R if r['tears_body_comps']),default=None),
       'navy_new_max':top('navy_interior_new'),'underlay_visible_max':top('underlay_flat_visible',2),
       'foot_line_off_max':sorted(fl,reverse=True)[:2],'foot_dx_max':sorted(fdx,reverse=True)[:2],
       'rest_foot_rows':{s:R[0]['foot'][s]['y'] if R[0]['foot'][s] else None for s in R[0]['foot']},
       'headAxis_frames':ha,'neck_jump_at_toggles':jump,'neck_max_step_elsewhere':round(other_max,4),'neck_range':[round(float(ns.min()),4),round(float(ns.max()),4)]}
    if verbose: print(json.dumps(s))
    return s
if __name__=='__main__':
    for n in sys.argv[1:]: summ(n)
