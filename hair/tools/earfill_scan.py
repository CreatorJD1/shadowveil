import sys, itertools; from earfill_lib import *
B={'apose':(530,20,820,370),'tpose':(530,20,830,360),'left':(540,20,845,330),'right':(515,20,830,330),'back':(545,20,820,345)}
def bad(px):  # premult float -> bool: shows background/white/chroma
    u=unpremul(px).astype(int); r,g,b,a=[u[...,i] for i in range(4)]
    return (a<255)|((r>240)&(g>240)&(b>240))|((b>r+40)&(b>g+40))
def groups(parts):
    by={p['id']:p for p in parts}; sw=lambda p:(p.get('swayWeight') or 0)>0 or (p.get('swayY') or 0)>0
    root={}
    for p in parts:
        q=p
        while q.get('parent') in by and sw(by[q['parent']]): q=by[q['parent']]
        if sw(p): root[p['id']]=q['id']
    G={}
    for i,r in root.items(): G.setdefault(r,[]).append(i)
    return G
def scan(v,hd=None,hair_back=None,shared_only=False):
    V=View(v,B[v],hd); rest=V.render(hair_back=hair_back); rb=bad(rest)
    SX=np.linspace(-1,1,41); SY=[-1,-0.5,-1/3,0,1/3,0.5,1]
    shared=np.zeros(rb.shape,bool)
    for sx in SX:
        for sy in SY: shared|=bad(V.render(sx,sy,hair_back))&~rb
    if shared_only: return V,rest,rb,shared,shared
    # independent drives: per chain group, find pixels the group covers opaquely at rest but can uncover
    # a pixel is revealable if static layers + mid don't cover it and every group can be moved off it simultaneously
    G=groups(V.parts); Mrest=matrices(V.parts,V.ymax,0,0)
    static=np.zeros(V.mid.shape); low=[p for p in V.order if p['layer']<200]
    # static coverage: hair_back (+bun if static), mid, static high parts
    def cov_of(ids,sx,sy):
        Ms=matrices(V.parts,V.ymax,sx,sy); a=np.zeros(rb.shape)
        for i in ids:
            im=V.img[i] if not (i=='hair_back' and hair_back is not None) else hair_back
            w=warp(im,Ms[i],V.box)[...,3]; a=1-(1-a)*(1-w/255)
        return a
    grouped=set(i for g in G.values() for i in g)
    st_ids=[p['id'] for p in V.parts if p['id'] not in grouped]
    stat=cov_of(st_ids,0,0); stat=1-(1-stat)*(1-V.mid[...,3]/255)
    # for each group: min coverage alpha over its poses (independent s per member, dy per member)
    free=np.ones(rb.shape,bool)
    for r,ids in G.items():
        mn=np.ones(rb.shape)
        vals=np.linspace(-1,1,21) if len(ids)>1 else SX
        combos=list(itertools.product(vals,repeat=len(ids)))
        for c in combos:
            for sy in [-1,0,1]:
                sxd={i:c[k] for k,i in enumerate(ids)}; syd={i:sy for i in ids}
                mn=np.minimum(mn,cov_of(ids,sxd,syd))
        free&=mn<0.999
    indep=free&(stat<0.999)&~rb
    return V,rest,rb,shared,indep|shared
if __name__=='__main__':
    for v in VIEWS:
        V,rest,rb,sh,ind=scan(v)
        np.save(f'/tmp/earfill_reveal_{v}.npy',np.stack([sh,ind]))
        print(v,'shared-slider revealed',sh.sum(),'independent-drive revealed',ind.sum(),flush=True)
