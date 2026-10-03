# Python mirror of rig/index.html pmDraw (partmesh v0.1, angle blend) for the hair lineart checker. Read-only on rig/partmesh/staged.
import json, numpy as np
from scipy import ndimage as ndi
I=[1,0,0,1,0,0]
def mul(a,b): return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]]
def inv(m):
    a,b,c,d,e,f=m; det=a*d-b*c; ia,ib,ic,id_=d/det,-b/det,-c/det,a/det; return [ia,ib,ic,id_,-(ia*e+ic*f),-(ib*e+id_*f)]
def rotAt(px,py,deg):
    if not abs(deg)>0: return I
    t=np.deg2rad(deg); c,s=np.cos(t),np.sin(t); return [c,s,-s,c,px-c*px+s*py,py-s*px-c*py]
def T(dx,dy): return [1,0,0,1,dx,dy]
def rel(Mp,Mc,c):
    D=mul(inv(Mp),Mc); a=np.degrees(np.arctan2(D[1],D[0])); x=D[0]*c[0]+D[2]*c[1]+D[4]-c[0]; y=D[1]*c[0]+D[3]*c[1]+D[5]-c[1]
    return dict(a=a,d=(x,y),c=c,id=abs(a)<1e-9 and abs(x)<1e-9 and abs(y)<1e-9)
def frac(J,t):
    if J is None or J['id'] or not t: return I
    return mul(T(t*J['d'][0],t*J['d'][1]),rotAt(J['c'][0],J['c'][1],t*J['a']))
def smooth(t): t=np.clip(t,0,1); return t*t*(3-2*t)
class PM:
    def __init__(s,path):
        j=json.load(open(path)); s.j=j; s.parts={p['id']:p for p in j['parts']}; s.joints=j['joints']
        for p in s.parts.values():
            d=p['drawings']['part']; p['V']=np.array(d['mesh']['vertices']); p['T']=np.array(d['mesh']['triangles']); p['W']=np.array(d['mesh']['weights']); p['pivot']=d['pivot']
    def joints_for(s,pid,Ms):
        p=s.parts[pid]; Mp=Ms.get(p['parent'],I) if p['parent'] else I; Mx=Ms[pid]
        Jr=rel(Mp,Mx,p['pivot']); Jc=rel(Mx,Ms[p['child']],s.joints[p['child']]['centre']) if p['child'] else None
        return Mp,Mx,Jr,Jc
    def ident(s,pid,Ms):
        _,_,Jr,Jc=s.joints_for(pid,Ms); return Jr['id'] and (Jc is None or Jc['id'])
    def weights_at(s,pid,x,y):
        p=s.parts[pid]; J=s.joints[pid]; n=np.array(J['axis']); sr=(np.array([x,y])-np.array(p['pivot']))@n; w=smooth((sr-J.get('blendOffset',0)+J['blend'])/(2*J['blend']))
        if p['child']:
            Jc=s.joints[p['child']]; nc=np.array(Jc['axis']); sc=(np.array([x,y])-np.array(Jc['centre']))@nc; u=smooth((sc-Jc.get('blendOffset',0)+Jc['blend'])/(2*Jc['blend']))
        else: u=0.0
        return w,u
    def Mv(s,pid,Ms,w,u):
        Mp,Mx,Jr,Jc=s.joints_for(pid,Ms); return mul(Mp,mul(frac(Jr,w),frac(Jc,u)))
    def fwd(s,pid,Ms,x,y):
        w,u=s.weights_at(pid,x,y); M=s.Mv(pid,Ms,w,u); return M[0]*x+M[2]*y+M[4], M[1]*x+M[3]*y+M[5]
    def back(s,pid,Ms,X,Y):
        x,y=X,Y
        for _ in range(12):
            w,u=s.weights_at(pid,x,y); M=inv(s.Mv(pid,Ms,w,u)); x,y=M[0]*X+M[2]*Y+M[4], M[1]*X+M[3]*Y+M[5]
        return x,y
    def deformed(s,pid,Ms):
        p=s.parts[pid]; out=np.zeros_like(p['V'])
        for i,(x,y) in enumerate(p['V']):
            M=s.Mv(pid,Ms,p['W'][i,0],p['W'][i,1]); out[i]=[M[0]*x+M[2]*y+M[4], M[1]*x+M[3]*y+M[5]]
        return out
    def warp(s,pid,img,Ms,box):
        """mesh draw like the GL path: pixel centres inside each deformed triangle, bilinear source sample (premultiplied)."""
        p=s.parts[pid]; V=p['V']; D=s.deformed(pid,Ms); x0,y0,x1,y1=box; H,W=y1-y0,x1-x0
        sx=np.full((H,W),-1e9); sy=np.full((H,W),-1e9); hit=np.zeros((H,W),bool)
        for t in p['T']:
            A=D[t]; S=V[t]
            bx0=int(np.floor(A[:,0].min()-0.5)); bx1=int(np.ceil(A[:,0].max()+0.5)); by0=int(np.floor(A[:,1].min()-0.5)); by1=int(np.ceil(A[:,1].max()+0.5))
            bx0=max(bx0,x0); by0=max(by0,y0); bx1=min(bx1,x1); by1=min(by1,y1)
            if bx0>=bx1 or by0>=by1: continue
            yy,xx=np.mgrid[by0:by1,bx0:bx1]; px=xx+.5; py=yy+.5
            (ax,ay),(bx,by),(cx,cy)=A; den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(den)<1e-12: continue
            l1=((by-cy)*(px-cx)+(cx-bx)*(py-cy))/den; l2=((cy-ay)*(px-cx)+(ax-cx)*(py-cy))/den; l3=1-l1-l2
            m=(l1>=-1e-9)&(l2>=-1e-9)&(l3>=-1e-9)
            if not m.any(): continue
            qx=l1*S[0,0]+l2*S[1,0]+l3*S[2,0]; qy=l1*S[0,1]+l2*S[1,1]+l3*S[2,1]
            Y,X=yy[m]-y0,xx[m]-x0; sx[Y,X]=qx[m]; sy[Y,X]=qy[m]; hit[Y,X]=True
        out=np.zeros((H,W,4))
        ys,xs=np.nonzero(hit)
        for k in range(4): out[ys,xs,k]=ndi.map_coordinates(img[...,k],[sy[ys,xs]-.5,sx[ys,xs]-.5],order=1,mode='constant',cval=0)
        return out
