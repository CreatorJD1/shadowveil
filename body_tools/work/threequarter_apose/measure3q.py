import numpy as np, json, math, sys, os
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0,'/workspace/shadowveil/body_tools/work/apose_turn')
from measure import measure, runs
ROOT='/workspace/shadowveil'
def load(f):
    a=np.array(Image.open(f).convert('RGBA')); return a
def bbox(m):
    ys,xs=np.nonzero(m); return None if not len(ys) else [int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
def head_height(a,m,top):
    L=a[...,:3].astype(int).mean(-1); dark=m&(L<70)
    hb=m[top:top+260]; cx=int(np.median(np.nonzero(hb)[1]))
    skin=m&(a[...,0].astype(int)-a[...,2]>60)&(L>90)
    best=None
    for y in range(top+200,top+300):
        xs=[x for x in range(cx-70,cx+70) if dark[y,x] and skin[y-4,x] and skin[y+4,x]]
        if len(xs)>=2: best=y
    return (best-top) if best else None, best
def arm_detail(m,arm):
    """walk armpit->tip; wrist = narrowest perpendicular width 100-220 px back from the tip."""
    ax,ay=arm['armpit']; tx,ty=arm['tip']; L=math.hypot(tx-ax,ty-ay); ux,uy=(tx-ax)/L,(ty-ay)/L; px,py=-uy,ux
    def width(t):
        cx,cy=ax+ux*t,ay+uy*t; w=0; 
        for sgn in (1,-1):
            k=0
            while k<80:
                x=int(round(cx+sgn*px*k)); y=int(round(cy+sgn*py*k))
                if not(0<=x<m.shape[1] and 0<=y<m.shape[0]) or not m[y,x]: break
                k+=1
            w+=k
        return w
    ws=[(width(t),t) for t in np.arange(max(40,L-230),L-90,1.0)]
    ws=[q for q in ws if q[0]>4]
    if not ws: return None
    wmin=min(q[0] for q in ws); tw=max(t for w,t in ws if w<=wmin+2); hand=L-tw  # wrist = distal end of the narrow wrist plateau
    # finger runs: perpendicular cut 22 px back from the tip
    def runs_at(t):
        cx,cy=ax+ux*t,ay+uy*t; vals=[]
        for k in range(-70,71):
            x=int(round(cx+px*k)); y=int(round(cy+py*k)); vals.append(bool(0<=x<m.shape[1] and 0<=y<m.shape[0] and m[y,x]))
        v=np.array(vals,int); return int(((v[1:]-v[:-1])==1).sum()+v[0])
    return dict(wrist_w=int(wmin),armpit_to_wrist=round(float(tw),1),hand_len=round(float(hand),1),reach=round(float(L),1),finger_runs={str(d):runs_at(L-d) for d in (15,25,35)})
def feet(m,foot):
    out=[]; band=m[foot-45:foot+1]; lab,n=nd.label(band)
    for i in range(1,n+1):
        ys,xs=np.nonzero(lab==i)
        if len(xs)>150: out.append(dict(x0=int(xs.min()),x1=int(xs.max()),len_x=int(xs.max()-xs.min()+1)))
    return sorted(out,key=lambda d:d['x0'])
def all_metrics(f):
    a=load(f); m=a[...,3]>0
    o=measure(m); top=o['top']
    hh,chin=head_height(a,m,top)
    arms={k:arm_detail(m,v) for k,v in o['arms'].items()}
    return dict(top=o['top'],foot=o['foot'],H=o['H'],shoulder_w=o['shoulder_w'],leg_len=o['leg_len'],crotch_y=o['crotch_y'],ankle_y=o['ankle_y'],
                head_h=hh,chin_y=chin,arms=arms,feet=feet(m,o['foot']),
                bun_w_at_crown30=len(np.nonzero(m[top+30])[0]) if True else None)
if __name__=='__main__':
    for f in sys.argv[1:]: print(f,json.dumps(all_metrics(f)))
