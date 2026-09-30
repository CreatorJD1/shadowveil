import json,numpy as np
R=json.load(open('silhouette.json')); W=np.array([r['right']-r['left']+1 for r in R],float); n=len(W)
from scipy.ndimage import uniform_filter1d
Ws=uniform_filter1d(W,5,mode='nearest')
p1=30+int(np.argmin(Ws[30:90])); bk=p1+int(np.argmax(Ws[p1:p1+80])); p2=bk+int(np.argmin(Ws[bk:bk+80]))
print('front0 W',W[0],'p1',p1,W[p1],'back',bk,W[bk],'p2',p2,W[p2],'end',W[-1])
th=np.zeros(n)
def q(w,a,b): return np.degrees(np.arccos(np.sqrt(np.clip((w*w-b*b)/(a*a-b*b),0,1))))
for i in range(n):
    w=Ws[i]
    if i<=p1: th[i]=q(w,Ws[0],Ws[p1])
    elif i<=bk: th[i]=180-q(w,Ws[bk],Ws[p1])
    elif i<=p2: th[i]=180+q(w,Ws[bk],Ws[p2])
    else: th[i]=360-q(w,Ws[-1],Ws[p2])
json.dump(dict(theta=th.tolist(),W=W.tolist(),p1=p1,back=bk,p2=p2),open('theta.json','w'))
for t in range(0,360,45):
    tt=t if t else 0
    cand=np.argsort(np.abs(((th-tt+180)%360)-180))[:1]
    print(t,'closest frame',int(cand[0]),'theta',round(th[cand[0]],1))
print('f360-> end theta',round(th[-1],1))
print(' '.join(f'{i}:{th[i]:.0f}' for i in range(0,n,5)))
