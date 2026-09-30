import numpy as np, json, sys
sys.argv=['x']; exec(open('analyze_motion.py').read().split("if __name__")[0])
def sublag(a,b,fps,maxlag=8):
    (L,c),res=xcorr_lag(a,b,maxlag); d=dict(res)
    if abs(L)<maxlag: 
        y0,y1,y2=d[L-1],d[L],d[L+1]; den=y0-2*y1+y2; off=0.5*(y0-y2)/den if den!=0 else 0
    else: off=0
    return round(1000*(L+off)/fps,1),round(c,2)
out={}
for tag in ['sway','nod','run','jump','side','idle','idle-long','look','back','stop']+(['walk'] if __import__('os').path.exists('/tmp/gr/sig_walk.npz') else []):
    D=dict(np.load(f'/tmp/gr/sig_{tag}.npz')); fps=float(D['fps'])
    fx,fy,tilt=sm(D['fx']),sm(D['fy']),sm(D['tilt'])
    bx,by,lx,ly=sm(D['bx']),sm(D['by']),sm(D['lx']),sm(D['ly'])
    ang=fill(np.nanmean(np.vstack([sm(D['angL']),sm(D['angR'])]),0))
    bab=np.degrees(np.arctan2(bx-fx,-(by-fy)))
    g=np.gradient
    out[tag]=dict(headY_bunY=sublag(g(fy),g(by),fps),headY_strandY=sublag(g(fy),g(ly),fps),headX_bunX=sublag(g(fx),g(bx),fps),headX_strandX=sublag(g(fx),g(lx),fps),
                  tilt_bunAng=sublag(g(tilt),g(bab),fps),tilt_strandAng=sublag(g(tilt),g(ang),fps))
    print(tag,out[tag])
json.dump(out,open('subframe_lags.json','w'),indent=1)
