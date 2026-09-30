"""Offline port of rig/index.html stepHair + headPose, driven by puppet export clips.
Read-only on the project; writes only into hair/qa/export_check/."""
import json, math, sys, os
ROOT='/workspace/shadowveil'; OUT=ROOT+'/hair/qa/export_check'
EXP=ROOT+'/reference/grok_build/public/puppet/export/clips'
VIEWS=['apose','tpose','left','right','back']
CLIPS=['hinge','wave','look','idle','reach','twist','collapse']
SETTINGS={'current':dict(fr=1.1,zr=0.3,fc=1.0,zc=0.3,sm=0.09,g=0.8),
          'A':dict(fr=4.0,zr=0.8,fc=4.0,zc=0.8,sm=0.03,g=0.4),
          'B':dict(fr=2.0,zr=0.6,fc=2.0,zc=0.6,sm=0.05,g=0.8)}
# puppet skeleton (src/lib/puppet/mesh.ts), normalized on 512x1100 canvas
PJ={'torso':(None,0.5,0.512),'hinge':('torso',0.5,0.368),'neck':('hinge',0.506,0.208),'head':('neck',0.506,0.155)}
PW,PH=512,1100
def clamp(x,a,b): return a if x<a else b if x>b else x
def fnv(s):
    h=2166136261
    for ch in s: h=((h^ord(ch))*16777619)&0xffffffff
    return h/4294967296
def rot(a):  # canvas rotate, + clockwise with y down
    r=math.radians(a); return (math.cos(r),math.sin(r),-math.sin(r),math.cos(r))
def load_view(v):
    hair=json.load(open(f'{ROOT}/views/{v}/hair/rig.json'))['parts']
    body=json.load(open(f'{ROOT}/views/{v}/body/rig.json'))
    tp=[p for p in body['parts'] if p['id']=='torso'][0]
    by={p['id']:p for p in hair}; sw=lambda p:(p.get('swayWeight') or 0)>0; info={}
    for p in hair:
        q=p;d=0
        while q.get('parent') and q['parent'] in by and sw(by[q['parent']]): q=by[q['parent']]; d+=1
        par=p['parent'] if (p.get('parent') and p['parent'] in by and sw(by[p['parent']])) else None
        info[p['id']]=dict(root=q['id'],depth=d,parent=par,sway=sw(p))
    hf=by['hair_front']
    return dict(hair=hair,info=info,torso=(tp['pivotX'],tp['pivotY'],tp.get('maxRotDeg',8)),hf=(hf['pivotX'],hf['pivotY']))
def clip_frames(c):
    d=json.load(open(f'{EXP}/{c}.json')); return d['duration'],d['fps'],[f['joints'] for f in d['frames']]
def sample(frames,fps,dur,u):  # periodic linear interp in clip time u in [0,dur)
    n=len(frames); x=(u%dur)*fps; i=int(math.floor(x))%n; k=x-math.floor(x); j=(i+1)%n
    return {key:frames[i][key]*(1-k)+frames[j][key]*k for key in ('torso','hinge','neck','head')}
def head_pose(V,J,mode):
    tx,ty,_=V['torso']; hx,hy=V['hf']
    if mode.startswith('rig'):  # our rig: BodyLean only (hinge -> BodyLean, clamped to Body limit), head rigid child of torso
        L=float(mode[3:]); a=clamp(J['hinge'],-L,L)
        c,s,_,_=rot(a); dx,dy=hx-tx,hy-ty
        return a, tx+c*dx-s*dy, ty+s*dx+c*dy
    # 'ref': full puppet chain torso->hinge->neck->head mapped onto our canvas (scale by torso-root..head-top span)
    top=41.0; sc=(ty-top)/((PJ['torso'][2]-0.085)*PH)
    P=lambda k:(tx+(PJ[k][1]-PJ['torso'][1])*PW*sc, ty+(PJ[k][2]-PJ['torso'][2])*PH*sc)
    M=(1,0,0,1,0,0); ang=0
    for k in ('torso','hinge','neck','head'):
        px,py=P(k); a=J[k]; ang+=a; c,s,_,_=rot(a)
        # M = M * T(p) R T(-p)
        R=(c,s,-s,c,px-c*px+s*py,py-s*px-c*py)
        M=mul(M,R)
    return ang, M[0]*hx+M[2]*hy+M[4], M[1]*hx+M[3]*hy+M[5]
def mul(a,b): return (a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5])
def simulate(V,S,drive,T,dt=1/60,wind=True):
    """drive(t)->(a,x,y) head pose. returns list of per-step dicts id->(x,xraw)"""
    hair=V['hair'];info=V['info'];order=sorted(hair,key=lambda p:info[p['id']]['depth'])
    st={};prev=None;t=0.0;rec=[]
    for step in range(int(round(T/dt))):
        t+=dt; hp=drive(t); pv=prev or hp
        vx=(hp[1]-pv[1])/dt; vy=(hp[2]-pv[2])/dt; va=(hp[0]-pv[0])/dt; prev=hp; out={}
        for p in order:
            inf=info[p['id']]
            if not inf['sway']: continue
            s=st.setdefault(p['id'],dict(x=0.,vx=0.,y=0.,vy=0.,lx=None,ly=None))
            ph=fnv(inf['root'])*math.pi*2; d=inf['depth']; W=1.0 if wind else 0.0
            if not inf['parent']:
                txx=clamp(-hp[0]/6,-1,1)*S['g']+W*(0.16*math.sin(2*math.pi*0.23*t+ph)+0.07*math.sin(2*math.pi*0.61*t+1.7*ph))
                tyy=W*0.12*math.sin(2*math.pi*0.31*t+ph); f=S['fr']; z=S['zr']
                s['vx']+=(-vx*0.004-va*0.02)*dt*60*0.05; s['vy']+=(-vy*0.004)*dt*60*0.05
            else:
                q=out[inf['parent']]
                if s['lx'] is None: s['lx'],s['ly']=q[0],q[3]
                k=clamp(dt/S['sm'],0,1); s['lx']+=(q[0]-s['lx'])*k; s['ly']+=(q[3]-s['ly'])*k
                txx=s['lx']*0.9+W*0.04*math.sin(2*math.pi*0.4*t+ph+d); tyy=s['ly']*0.8; f=S['fc']; z=S['zc']
            K=(2*math.pi*f)**2; D=2*z*2*math.pi*f; n=max(1,math.ceil(dt/(1/120)-1e-9)); h=dt/n
            for _ in range(n):
                s['vx']+=(K*(txx-s['x'])-D*s['vx'])*h; s['x']+=s['vx']*h; s['vy']+=(K*(tyy-s['y'])-D*s['vy'])*h; s['y']+=s['vy']*h
            raw=s['x']; s['x']=clamp(s['x'],-1,1); s['y']=clamp(s['y'],-1,1)
            out[p['id']]=(s['x'],raw,txx,s['y'])
        rec.append((t,hp,out))
    return rec
