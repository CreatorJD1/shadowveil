# Exact, vectorised forbidden-region sweep for chained hair (contract v1.3: every segment's drive s is independent).
# For a part P with swaying ancestors A1..Ak (root first), world = R(A1)...R(Ak) R(P) with R(q)=rotAt(pivot_q, w_q*deg_q*s_q)
# (same recursion as rig/index.html chain()), then dy=round(s_y*swayY*swayYMaxPx) on P only. Coverage is exact for
# bilinear drawImage: output pixel (i,j) is touched iff its centre, mapped back to source index space, lies strictly
# within 1 px (L-inf) of a source pixel with alpha>0.
import numpy as np, itertools
def rot(px,py,deg):
    t=np.deg2rad(deg); c,s=np.cos(t),np.sin(t)
    return np.array([[c,-s,px-c*px+s*py],[s,c,py-s*px-c*py],[0,0,1.0]])
def jsround(x): return np.floor(np.asarray(x)+0.5).astype(int)
S_OWN=sorted(set([-1,-.5,.5,1]+list(np.round(np.linspace(-1,1,41),3))))
S_ANC=list(np.round(np.linspace(-1,1,21),3))
OFF=np.array([(a,b) for a in (-1,0,1) for b in (-1,0,1)])
def dys(e,ymax):
    return sorted(set(jsround(np.linspace(-1,1,41)*min(1,max(0,e.get('swayY',0)))*ymax).tolist()))
def hits(e,chain_,mask,forb,ymax,s_own=S_OWN,s_anc=S_ANC,chunk=4000):
    """chain_=[ancestor parts root..parent] (swaying only; fixed parents contribute identity). Returns hit count."""
    H,W=forb.shape; ys,xs=np.nonzero(mask)
    if len(xs)==0: return 0
    P=np.stack([xs+.5,ys+.5,np.ones(len(xs))])            # 3xN source centres
    parts=chain_+[e]; grids=[s_anc]*len(chain_)+[s_own]
    mats=[]
    for p,g in zip(parts,grids):
        a=(p.get('swayWeight') or 0)*(p.get('maxSwayDeg') or 0)
        mats.append(np.stack([rot(p['pivotX'],p['pivotY'],a*s) for s in g]))
    combos=np.array(list(itertools.product(*[range(len(g)) for g in grids])))
    DY=dys(e,ymax); tot=0
    # forbidden lookup with all dy shifts folded in: F2[y,x]=any forb[y+dy,x] for dy in DY  (part moves by dy)
    F2=np.zeros_like(forb)
    for dy in DY:
        if dy>=0: F2[:H-dy]|=forb[dy:]
        else: F2[-dy:]|=forb[:H+dy]
    for c0 in range(0,len(combos),chunk):
        cb=combos[c0:c0+chunk]
        M=mats[0][cb[:,0]]
        for k in range(1,len(parts)): M=M@mats[k][cb[:,k]]
        F=M@P                                              # C x 3 x N
        fx,fy=F[:,0],F[:,1]; L=M[:,:2,:2]                  # linear part (rotation)
        bx=np.floor(fx).astype(int); by=np.floor(fy).astype(int)
        for ox,oy in OFF:
            cx=bx+ox; cy=by+oy; dx=cx+.5-fx; dyv=cy+.5-fy
            # back to source frame: inverse rotation = transpose
            u=L[:,0,0,None]*dx+L[:,1,0,None]*dyv; v=L[:,0,1,None]*dx+L[:,1,1,None]*dyv
            ok=(np.abs(u)<1)&(np.abs(v)<1)&(cx>=0)&(cx<W)&(cy>=0)&(cy<H)
            if ok.any(): tot+=int(F2[cy[ok],cx[ok]].sum())
    return tot
