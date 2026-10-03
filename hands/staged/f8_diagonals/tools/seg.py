# F8 step 2: label map for a near hand at frame scale: palm, Index/Middle/Ring/Pinky 1-3, Thumb1-3 + pivots.
# Tips = geodesic extremities from the wrist cut; valleys = deepest point of each key gap between neighbouring tips;
# knuckle line through the inter-finger valleys; px assigned to the nearest centreline (palm axis, finger and thumb polylines).
import json,sys,numpy as np
from scipy import ndimage as nd
from skimage.graph import MCP_Geometric
PROP=dict(finger=(0.45,0.30,0.25),thumb=(0.40,0.33,0.27))
def geod(m,seed):
    cost=np.where(m,1.0,np.inf);mcp=MCP_Geometric(cost);D,_=mcp.find_costs(list(zip(*np.nonzero(seed))));D[~m]=np.inf;return D
def tips(m,D,n=5,r=7,minfrac=0.45):
    from skimage.morphology import skeletonize
    sk=skeletonize(nd.binary_opening(m,iterations=1));nb=nd.convolve(sk.astype(int),np.ones((3,3)),mode='constant')-sk
    ends=np.argwhere(sk&(nb==1));jun=sk&(nb>=3);Df=np.where(np.isfinite(D),D,-1);dmax=Df.max();out=[]
    for y,x in ends:
        # walk the branch back to a junction: branch length = D(end) - D(junction px nearest along skeleton)
        lab,_=nd.label(sk&~nd.binary_dilation(jun,iterations=1),structure=np.ones((3,3)));br=lab==lab[y,x]
        if lab[y,x]==0: continue
        L=Df[y,x]-Df[br].min()
        if Df[y,x]>minfrac*dmax and L>=5:
            # snap to the farthest mask px within 3 px of the skeleton end
            yy,xx=np.mgrid[max(0,y-4):y+5,max(0,x-4):x+5];sel=m[yy,xx];j=np.argmax(np.where(sel,Df[yy,xx],-1));out.append((yy.ravel()[j],xx.ravel()[j],L))
    out=sorted(out,key=lambda t:-Df[t[0],t[1]])[:n];return [(a,b) for a,b,_ in out]
def tips_old(m,D,n=5,r=7,minfrac=0.45):
    Df=np.where(np.isfinite(D),D,-1);out=[];dmax=Df.max()
    # extremity = px whose D is max within an r-disk of the mask
    mx=nd.maximum_filter(Df,footprint=np.ones((2*r+1,2*r+1)))
    cand=np.argwhere((Df==mx)&(Df>minfrac*dmax));cand=sorted(cand.tolist(),key=lambda p:-Df[p[0],p[1]])
    for y,x in cand:
        if all(np.hypot(y-a,x-b)>r+2 for a,b in out): out.append((y,x))
    return out[:n]
def seg(z,thumb_sign,ntips=5,override=None):
    A=z['alpha'];m=A>0;pu,pv,w,u,v=z['pu'],z['pv'],z['w'],z['u'],z['v']
    seed=m&(pu<=-1);D=geod(m,seed)
    T=tips(m,D) if override is None or 'tips' not in override else [tuple(t) for t in override['tips']]
    T=[np.array([x,y],float) for y,x in T]                      # (x,y)
    rel=lambda p:np.array([(p-w)@u,(p-w)@v])
    T=sorted(T,key=lambda p:rel(p)[1]*thumb_sign,reverse=True)   # thumb side first
    # thumb = the tip on the thumb side with the shortest reach, if it is the first in v order
    th=T[0];fing=T[1:]
    if thumb_sign*rel(th)[1]<0: raise SystemExit('thumb not on thumb side')
    names=['Index','Middle','Ring','Pinky']
    # valleys between neighbouring tips (thumb-index, index-middle, ...): deepest (min D of the adjacent hand px) gap px
    def valley(a,b):
        n=int(np.hypot(*(a-b)))*2+2;P=[a+(b-a)*t for t in np.linspace(0,1,n)];bgp=[p for p in P if not m[int(round(p[1])),int(round(p[0]))]]
        from skimage.morphology import convex_hull_image;hull=convex_hull_image(m)
        gap=hull&~m;lab,_=nd.label(gap);ks={lab[int(round(p[1])),int(round(p[0]))] for p in bgp}-{0}
        if not ks:  # fingers touch: valley = min-D px on the segment
            Pm=[p for p in P if m[int(round(p[1])),int(round(p[0]))]];return min(Pm,key=lambda p:D[int(round(p[1])),int(round(p[0]))])
        g=np.isin(lab,list(ks));adj=nd.binary_dilation(g)&m;ys,xs=np.nonzero(adj);j=np.argmin(D[ys,xs]);return np.array([xs[j],ys[j]],float)
    V=[valley(T[i],T[i+1]) for i in range(len(T)-1)]   # V[0]=thumb/index, V[1]=I/M, V[2]=M/R, V[3]=R/P
    if override and 'valleys' in override: V=[np.array(p,float) for p in override['valleys']]
    # finger base (knuckle) points: middle of the two flanking inter-finger valleys; Index/Pinky outer flank extrapolated
    K=[V[1],V[2],V[3]];sp=[K[1]-K[0],K[2]-K[1]]
    flank=[K[0]-sp[0],K[0],K[1],K[2],K[2]+sp[1]]
    base=[(flank[i]+flank[i+1])/2 for i in range(4)]
    # thumb base (Thumb1 pivot): on the thumb-side wrist edge, a quarter of the way to the thumb valley
    tb=w+u*max(2.0,0.25*rel(V[0])[0])+v*thumb_sign*0.25*np.hypot(*(z['w']-z['w']))  # placeholder, refined below
    ys,xs=np.nonzero(m&(np.abs(pu)<1.5));side=[(x,y) for x,y in zip(xs,ys) if thumb_sign*pv[y,x]>0]
    wedge=np.array(max(side,key=lambda p:thumb_sign*pv[p[1],p[0]]),float) if side else w
    tb=w+(wedge-w)*0.55+u*4
    lines={'palm':[w,(base[1]+base[2])/2]}
    for i,nm in enumerate(names): lines[nm]=[base[i],fing[i]]
    lines['Thumb']=[tb,th]
    # nearest polyline (segment) owner
    yy,xx=np.mgrid[:m.shape[0],:m.shape[1]];P=np.stack([xx,yy],-1).astype(float)
    def dseg(a,b):
        ab=b-a;t=np.clip(((P-a)@ab)/max(ab@ab,1e-9),0,1);return np.hypot(*(P-(a+t[...,None]*ab)).transpose(2,0,1)),t
    keys=list(lines);dist=[];tt={}
    for k in keys:
        d,t=dseg(*lines[k]);dist.append(d);tt[k]=t
    own=np.argmin(np.stack(dist),0)
    # knuckle line: finger px on the palm side of the knuckle polyline go to the palm
    kn=np.array(flank);kpu=[rel(p)[0] for p in kn];kpv=[rel(p)[1] for p in kn]
    order=np.argsort(kpv);kn_u=np.interp(pv,np.array(kpv)[order],np.array(kpu)[order])
    lab=np.zeros(m.shape,'<U8')
    for i,k in enumerate(keys):
        sel=m&(own==i)
        if k in names:
            sel_p=sel&(pu<kn_u);lab[sel_p]='palm';sel=sel&~sel_p
        if k=='palm': lab[sel]='palm';continue
        t=tt[k];pr=PROP['thumb' if k=='Thumb' else 'finger'];c1,c2=pr[0],pr[0]+pr[1]
        if k in names:   # t measured from the knuckle base along base->tip
            lab[sel&(t<c1)]=k+'1';lab[sel&(t>=c1)&(t<c2)]=k+'2';lab[sel&(t>=c2)]=k+'3'
        else:
            lab[sel&(t<c1)]='Thumb1';lab[sel&(t>=c1)&(t<c2)]='Thumb2';lab[sel&(t>=c2)]='Thumb3'
    piv={'palm':w.tolist()}
    for k in names+['Thumb']:
        a,b=lines[k];pr=PROP['thumb' if k=='Thumb' else 'finger']
        piv[k+'1']=a.tolist();piv[k+'2']=(a+(b-a)*pr[0]).tolist();piv[k+'3']=(a+(b-a)*(pr[0]+pr[1])).tolist();piv[k+'_tip']=b.tolist()
    return lab,piv,dict(tips=[t.tolist() for t in T],valleys=[p.tolist() for p in V],base=[b.tolist() for b in base],thumb_base=tb.tolist())
