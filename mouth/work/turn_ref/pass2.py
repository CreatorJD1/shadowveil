import numpy as np, json
from scipy.optimize import brentq
from facemeas import *
P=json.load(open('tmp/pass1.json')); C=np.load('tmp/headcrops.npy',mmap_mode='r')
span=np.array([p['span'] for p in P],float); N=len(P)
def parab_min(i0,i1,sign):
    i=i0+int(np.argmin(sign*span[i0:i1])); y=sign*span[i-1:i+2]
    d=(y[0]-2*y[1]+y[2]); return i+(0.5*(y[0]-y[2])/d if d!=0 else 0)
p1=parab_min(40,80,1); bk=parab_min(90,130,-1); p2=parab_min(140,180,1)
B=float(span.min())
# ---- angle from arm span: s = A|cos| + B|sin| on the monotone branch; quadrant from the keyframes
def phi_from_span(s,A):
    f=lambda ph: A*np.cos(ph)+B*np.sin(ph)-s
    lo=np.arctan2(B,A)
    if s>=A*np.cos(lo)+B*np.sin(lo)-1e-9: return np.degrees(lo)
    if s<=B: return 90.0
    return np.degrees(brentq(f,lo,np.pi/2))
A_front=float(span[:4].mean()); A_back=float(span[int(bk)-2:int(bk)+3].max()); A_end=float(span[-10:].mean())
print('keyframes profile1 %.1f back %.1f profile2 %.1f'%(p1,bk,p2),'A',A_front,A_back,A_end,'B',B)
ang_span=[]; ang_time=[]
Q=[(0,p1,0,90,A_front),(p1,bk,90,180,A_back),(bk,p2,180,270,A_back),(p2,None,270,360,A_end)]
q_len=np.mean([p1-0,bk-p1,p2-bk])          # frames per 90 deg (for the last quadrant, where the end front is not an extremum)
for i in range(N):
    for (a,b_,t0,t1,A) in Q:
        if b_ is None or i<b_:
            if i<a: continue
            ph=phi_from_span(span[i],A)
            if t0 in (0,180): th=t0+ph            # leaving front/back: angle grows as span falls
            else: th=t0+(90-ph)                   # leaving profile: span grows back
            bb=b_ if b_ is not None else a+q_len
            ang_span.append(th); ang_time.append(t0+(t1-t0)*min((i-a)/(bb-a),1.5)); break
ang_span=np.array(ang_span); ang_time=np.array(ang_time)
json.dump(dict(p1=p1,back=bk,p2=p2,q_len=q_len,A=[A_front,A_back,A_end],B=B,ang_span=ang_span.tolist(),ang_time=ang_time.tolist()),open('tmp/angles.json','w'))
print(' '.join('%d:%.0f/%.0f'%(i,ang_span[i],ang_time[i]) for i in range(0,N,6)))
