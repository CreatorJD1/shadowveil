import numpy as np, json
A=json.load(open('tmp/angles.json')); P=json.load(open('tmp/pass1.json'))
span=np.array([p['span'] for p in P],float); N=len(span); p1,bk,p2=A['p1'],A['back'],A['p2']
fr=np.arange(N)
# middle half-turn: piecewise-linear time between measured keyframes (profile 90, back 180, profile 270)
th_mid=np.interp(fr,[p1,bk,p2],[90,180,270])
sel=(fr>=p1)&(fr<=p2)
c=np.abs(np.cos(np.radians(th_mid[sel]))); s=span[sel]
o=np.argsort(c); c,s=c[o],s[o]
# monotone fit span(c): running max after binning
bins=np.linspace(0,1,21); cb=[];sb=[]
for a,b in zip(bins[:-1],bins[1:]):
    m=(c>=a)&(c<b)
    if m.any(): cb.append(c[m].mean()); sb.append(s[m].mean())
cb=np.array(cb); sb=np.maximum.accumulate(np.array(sb))
def inv(sp): return float(np.interp(sp,sb,cb,left=0,right=1))
theta=th_mid.copy()
for i in range(N):
    if i<p1: theta[i]=np.degrees(np.arccos(min(1,inv(span[i]))))
    elif i>p2: theta[i]=360-np.degrees(np.arccos(min(1,inv(span[i]))))
json.dump(dict(theta=theta.tolist(),curve=dict(c=cb.tolist(),span=sb.tolist()),p1=p1,back=bk,p2=p2),open('tmp/theta.json','w'))
print('curve',list(zip(np.round(cb,2),np.round(sb))))
print(' '.join('%d:%.0f'%(i,theta[i]) for i in range(0,N,3)))
