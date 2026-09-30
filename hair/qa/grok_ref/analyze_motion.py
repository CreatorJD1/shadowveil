import numpy as np, json, sys, glob, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.ndimage import median_filter, uniform_filter1d
OUT='/workspace/shadowveil/hair/qa/grok_ref'
def fill(x):
    x=np.asarray(x,float).copy(); i=np.isfinite(x)
    if i.sum()<3: return x
    x[~i]=np.interp(np.where(~i)[0],np.where(i)[0],x[i]); return x
def sm(x,k=3): return uniform_filter1d(median_filter(fill(x),3),k)
def xcorr_lag(a,b,maxlag):
    a=a-a.mean(); b=b-b.mean(); best=(0,-2)
    res=[]
    for L in range(-maxlag,maxlag+1):
        if L>=0: x,y=a[:len(a)-L],b[L:]
        else: x,y=a[-L:],b[:len(b)+L]
        c=np.corrcoef(x,y)[0,1] if x.std()>0 and y.std()>0 else 0
        res.append((L,c))
        if c>best[1]: best=(L,c)
    return best,res
def spring(target,f,z,dt,x0,v0=0):
    K=(2*np.pi*f)**2; D=2*z*2*np.pi*f; x=x0; v=v0; out=[]; n=4; h=dt/n
    for t in target:
        for _ in range(n): v+=(K*(t-x)-D*v)*h; x+=v*h
        out.append(x)
    return np.array(out)
def fit_spring(head,hair,dt):
    off=np.median(hair-head); tgt=head+off
    rig=np.mean((hair-tgt)**2)
    best=None
    for f0 in [0.6,1.0,1.5,2.5,4]:
        for z0 in [0.2,0.5,0.9]:
            r=minimize(lambda p: np.mean((spring(tgt,abs(p[0])+1e-3,abs(p[1]),dt,hair[0])-hair)**2),[f0,z0],method='Nelder-Mead',options=dict(maxiter=300,xatol=1e-3,fatol=1e-4))
            if best is None or r.fun<best.fun: best=r
    f,z=abs(best.x[0]),abs(best.x[1]); var=np.var(hair)
    return dict(f_hz=f,zeta=z,mse_spring=best.fun,mse_rigid=rig,r2_spring=1-best.fun/var,r2_rigid=1-rig/var,gain=(rig-best.fun)/rig if rig>0 else 0)
def dom_period(x,fps):
    x=x-np.polyval(np.polyfit(np.arange(len(x)),x,2),np.arange(len(x)))
    if x.std()<1e-6: return np.nan,0
    ac=np.correlate(x,x,'full')[len(x)-1:]; ac/=ac[0]
    zc=np.where(np.diff(np.sign(ac))!=0)[0]
    if len(zc)==0: return np.nan,0
    seg=ac[zc[0]:]; 
    if len(seg)<3: return np.nan,0
    k=zc[0]+np.argmax(seg); return 1000*k/fps, ac[k]
def analyze(tag):
    D=dict(np.load(f'/tmp/gr/sig_{tag}.npz')); fps=float(D['fps']); dt=1/fps; n=int(D['n']); t=np.arange(n)*dt*1000
    hh=np.nanmedian(D['chin']-D['top'])  # head height px (hair top..chin)
    fx=sm(D['fx']); fy=sm(D['fy']); tilt=sm(D['tilt'],3)
    bx=sm(D['bx']); lx=sm(D['lx']); hx=sm(D['hx'])
    aL=sm(D['angL']); aR=sm(D['angR'])
    frel=fill(D.get('flow_hair_x',np.full(n,np.nan))-D.get('flow_face_x',np.full(n,np.nan))); frel[0]=0
    flrel=fill(D.get('flow_loose_x',np.full(n,np.nan))-D.get('flow_face_x',np.full(n,np.nan))); flrel[0]=0
    R={'clip':tag,'fps':fps,'frames':n,'duration_ms':round(n*dt*1000),'head_px':round(float(hh),1)}
    R['head_x_range_px']=round(float(np.ptp(fx)),1); R['head_tilt_range_deg']=round(float(np.ptp(tilt)),1); R['head_y_range_px']=round(float(np.ptp(fy)),1)
    # lag: head x vs bun x / loose-strand x (absolute), velocities
    maxlag=int(0.5*fps)
    for name,sig in [('bun',bx),('strands',lx)]:
        (L,c),_=xcorr_lag(np.gradient(fx),np.gradient(sig),maxlag)
        R[f'lag_{name}_ms']=round(1000*L/fps); R[f'lag_{name}_corr']=round(float(c),2)
        rel=sig-fx; R[f'{name}_rel_std_px']=round(float(np.std(rel)),2)
        R[f'fit_{name}']={k:round(float(v),3) for k,v in fit_spring(fx,sig,dt).items()}
        p,pc=dom_period(rel,fps); R[f'period_{name}_rel_ms']=None if not np.isfinite(p) else round(p); R[f'period_{name}_rel_acpeak']=round(float(pc),2)
    # tilt vs strand angle lag
    ang=np.nanmean(np.vstack([aL-np.nanmedian(aL),aR-np.nanmedian(aR)]),0); ang=fill(ang)
    (L,c),_=xcorr_lag(np.gradient(tilt),np.gradient(ang),maxlag)
    bab=np.degrees(np.arctan2(bx-fx,-(sm(D['by'])-fy)))
    (L2,c2),_=xcorr_lag(np.gradient(tilt),np.gradient(bab),maxlag)
    R['lag_tilt_to_bun_angle_ms']=round(1000*L2/fps); R['lag_tilt_bun_corr']=round(float(c2),2)
    R['bun_to_head_rotation_ratio']=round(float(np.polyfit(tilt,bab,1)[0]),2) if np.ptp(tilt)>2 else None
    (L3,c3),_=xcorr_lag(np.gradient(fy),np.gradient(sm(D['by'])),maxlag)
    R['lag_head_y_to_bun_y_ms']=round(1000*L3/fps); R['lag_bun_y_corr']=round(float(c3),2)
    (L4,c4),_=xcorr_lag(np.gradient(fy),np.gradient(sm(D['ly'])),maxlag)
    R['lag_head_y_to_strand_y_ms']=round(1000*L4/fps); R['lag_strand_y_corr']=round(float(c4),2)
    R['lag_tilt_to_strand_angle_ms']=round(1000*L/fps); R['lag_tilt_corr']=round(float(c),2)
    pd,pdc=dom_period(fx,fps); R['period_head_x_ms']=None if not np.isfinite(pd) else round(pd); R['period_head_acpeak']=round(float(pdc),2)
    # sway angle: strand-mass angle about temple, deviation from clip median, and minus head tilt
    R['max_sway_abs_deg']=round(float(np.nanpercentile(np.abs(ang),95)),1)
    R['max_sway_rel_head_deg']=round(float(np.nanpercentile(np.abs(ang-(tilt-np.median(tilt))),95)),1)
    bang=np.degrees(np.arctan2(bx-fx,-(sm(D['by'])-fy))); bang-=np.median(bang)
    R['max_bun_angle_deg']=round(float(np.nanpercentile(np.abs(bang-(tilt-np.median(tilt))),95)),1)
    # settle: head motion stops
    spd=uniform_filter1d(np.abs(np.gradient(fx))+np.abs(np.gradient(fy))+0.5*hh/50*np.abs(np.gradient(tilt)),5)
    noise=np.median(spd)
    thr=max(0.35, 0.15*np.percentile(spd,98))
    moving=spd>thr
    R['head_speed_thr_px_per_frame']=round(float(thr),2)
    st=None
    idx=np.where(moving)[0]
    if len(idx) and idx[-1] < n-int(0.8*fps) and np.percentile(spd,98)>1.0:
        st=idx[-1]+1
    R['motion_stop_ms']=None if st is None else round(1000*st/fps)
    rel=lx-fx; relb=bx-fx
    if st is not None:
        tail=rel[-int(0.6*fps):]; mu=tail.mean(); band=max(3*np.median(np.abs(tail-np.median(tail)))*1.4826,0.75)
        out=np.where(np.abs(rel[st:]-mu)>band)[0]
        R['settle_strands_ms']=round(1000*((out[-1]+1) if len(out) else 0)/fps); R['settle_band_px']=round(float(band),2)
        d=rel[st:]-mu; s=np.sign(np.where(np.abs(d)>band,d,0)); s=s[s!=0]
        R['overshoots_strands']=int((np.diff(s)!=0).sum())
        tailb=relb[-int(0.6*fps):]; mub=tailb.mean(); bandb=max(3*np.median(np.abs(tailb-np.median(tailb)))*1.4826,0.75)
        outb=np.where(np.abs(relb[st:]-mub)>bandb)[0]; R['settle_bun_ms']=round(1000*((outb[-1]+1) if len(outb) else 0)/fps)
        d=relb[st:]-mub; s=np.sign(np.where(np.abs(d)>bandb,d,0)); s=s[s!=0]; R['overshoots_bun']=int((np.diff(s)!=0).sum())
    # frame-to-frame jitter of strand mass at rest vs motion: generative flicker indicator
    R['strand_rel_jitter_px']=round(float(np.median(np.abs(np.diff(D['lx']-D['fx'])))),2)
    R['loose_px_cv']=round(float(np.nanstd(D['nloose'])/np.nanmean(D['nloose'])),2)
    # plot
    fig,ax=plt.subplots(4,1,figsize=(11,11),sharex=True)
    ax[0].plot(t,fx-fx.mean(),label='head (face centroid) x');ax[0].plot(t,bx-bx.mean(),label='bun x');ax[0].plot(t,lx-lx.mean(),label='loose strands x',alpha=.8)
    fb=R['fit_strands']; ax[0].plot(t,spring(fx+np.median(lx-fx),fb['f_hz'],fb['zeta'],dt,lx[0])-lx.mean(),'k--',lw=1,label=f"spring fit strands f={fb['f_hz']:.2f}Hz ζ={fb['zeta']:.2f} R²={fb['r2_spring']:.2f} (rigid {fb['r2_rigid']:.2f})")
    ax[0].set_ylabel('px (centred)');ax[0].legend(fontsize=7);ax[0].set_title(f"{tag}: fps {fps:g}, {n} frames, head≈{hh:.0f}px tall")
    ax[1].plot(t,rel-np.median(rel),label='strands x − head x');ax[1].plot(t,relb-np.median(relb),label='bun x − head x')
    ax[1].plot(t,np.cumsum(flrel)-np.cumsum(flrel).mean(),alpha=.6,label='∫ optical-flow(loose − face) x')
    if st is not None: ax[1].axvline(1000*st/fps,color='r',ls=':',label='head motion stops')
    ax[1].set_ylabel('px');ax[1].legend(fontsize=7)
    ax[2].plot(t,tilt-np.median(tilt),label='head tilt');ax[2].plot(t,ang,label='strand-mass angle about temple (dev.)');ax[2].plot(t,bang,label='bun angle (dev.)');ax[2].set_ylabel('deg');ax[2].legend(fontsize=7)
    ax[3].plot(t,spd,label='head speed');ax[3].axhline(thr,color='r',ls=':');ax[3].plot(t,D['nloose']/np.nanmax(D['nloose']),label='loose px count (norm)',alpha=.6);ax[3].set_xlabel('ms');ax[3].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f'{OUT}/motion_{tag}.png',dpi=80); plt.close(fig)
    return R
if __name__=='__main__':
    tags=sys.argv[1:] or sorted(os.path.basename(p)[4:-4] for p in glob.glob('/tmp/gr/sig_*.npz'))
    allr=[analyze(t) for t in tags]
    for r in allr: print(json.dumps(r))
    json.dump(allr,open(f'{OUT}/motion_metrics.json','w'),indent=1)
