# Step/ramp response of the rig's hair spring (same integrator as rig/index.html stepHair: dt=1/60 frames, semi-implicit Euler substeps of <=1/120 s)
import math,sys
def sim(fr,zr,fc,zc,lp,inp,T=4.0,dt=1/60):
    K=lambda f:(2*math.pi*f)**2; D=lambda f,z:2*z*2*math.pi*f
    r={'x':0,'v':0}; c={'x':0,'v':0,'lx':0}; out=[]; t=0
    n=max(1,math.ceil(dt/(1/120)-1e-9)); h=dt/n
    for i in range(int(round(T/dt))):
        t+=dt; tx=inp(t)
        for _ in range(n):
            r['v']+=(K(fr)*(tx-r['x'])-D(fr,zr)*r['v'])*h; r['x']+=r['v']*h
        k=min(1,max(0,dt/lp)) if lp>0 else 1; c['lx']+=(r['x']-c['lx'])*k; ctx=c['lx']*0.9
        for _ in range(n):
            c['v']+=(K(fc)*(ctx-c['x'])-D(fc,zc)*c['v'])*h; c['x']+=c['v']*h
        out.append((t,tx,r['x'],c['x']))
    return out
def metrics(fr,zr,fc,zc,lp):
    s=sim(fr,zr,fc,zc,lp,lambda t:1.0)
    res={}
    for name,idx,fin in (('root',2,1.0),('tip',3,0.9)):
        xs=[o[idx] for o in s]; pk=max(xs); ov=max(0,(pk-fin)/fin*100)
        st=0
        for o in s:
            if abs(o[idx]-fin)>0.02*fin: st=o[0]
        # first peak time (swing), damped period from successive peaks
        peaks=[s[i][0] for i in range(1,len(s)-1) if xs[i]>xs[i-1] and xs[i]>=xs[i+1] and xs[i]>fin]
        # ramp lag: steady-state delay behind a slow ramp
        rr=sim(fr,zr,fc,zc,lp,lambda t:0.1*t,T=6.0); tt,tx,xr,xc=rr[-1]
        lag=(tx-(xr if name=='root' else xc/0.9))/0.1
        res[name]=dict(overshoot_pct=round(ov,1),settle2_s=round(st,3),first_peak_s=round(peaks[0],3) if peaks else None,peaks=len(peaks),ramp_lag_ms=round(lag*1000,1),ramp_lag_frames30=round(lag*30,2))
    zr_=zr; res['theory_root']=dict(damped_period_s=round(1/(fr*math.sqrt(1-zr_**2)),3) if zr_<1 else None,overshoot_pct=round(100*math.exp(-math.pi*zr_/math.sqrt(1-zr_**2)),1) if zr_<1 else 0)
    return res
if __name__=='__main__':
    import json
    cfgs={'default':(1.1,0.3,1.0,0.3,0.09)}
    for a in sys.argv[1:]:
        n,v=a.split('='); cfgs[n]=tuple(map(float,v.split(',')))
    for n,c in cfgs.items(): print(n,c,json.dumps(metrics(*c)))
