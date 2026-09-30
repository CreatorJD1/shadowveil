import sys,json,numpy as np
from PIL import Image
sys.path.insert(0,'/workspace/gb'); from tracks import track; from fingers import analyse
def fan(cs):
    a=[q['ang'] for q in cs]
    if len(a)!=5: return None
    g0=abs(a[1]-a[0]); g4=abs(a[4]-a[3])
    if g0>=g4: th,f=a[0],a[1:]      # thumb at the low end
    else: th,f=a[4],a[3::-1]
    return dict(thumb_index=abs(th-f[0]) if g0>=g4 else abs(th-f[0]),adj=[abs(f[k+1]-f[k]) for k in range(3)],index_pinky=abs(f[3]-f[0]))
def clip(c,side,a,b):
    tr,F=track(c); t=tr[side]; R=[]
    for i in range(a,b):
        r=analyse(F[i],t['x'][i],t['y'][i],None); cs=[q for q in r['comps'] if q['len']>25]; f=fan(cs)
        if f: R.append((i,f))
    if not R: return None
    ip=np.array([f['index_pinky'] for _,f in R]); ti=np.array([f['thumb_index'] for _,f in R]); adj=np.array([f['adj'] for _,f in R])
    return dict(frames=len(R),of=b-a,index_pinky=(round(float(np.median(ip))),round(float(ip.max())),R[int(ip.argmax())][0]),thumb_index=(round(float(np.median(ti))),round(float(ti.max())),R[int(ti.argmax())][0]),adj_median=np.median(adj,0).round(0).tolist(),adj_max=adj.max(0).round(0).tolist())
def ours(view,side):
    r=json.load(open(f'/workspace/shadowveil/views/{view}/hands/rig.json')); d={}
    for f in ['Thumb','Index','Middle','Ring','Pinky']:
        m=None
        for k in (1,2,3):
            p=[q for q in r['parts'] if q['id']==f'{side}_{f}{k}'][0]; a=np.array(Image.open(f'/workspace/shadowveil/views/{view}/hands/{p["file"]}').convert('RGBA'))[...,3]>127
            m=a if m is None else m|a
        p1=[q for q in r['parts'] if q['id']==f'{side}_{f}1'][0]
        ys,xs=np.nonzero(m); P=np.stack([xs,ys],1).astype(float); mu=P.mean(0); d_=np.linalg.svd(P-mu,full_matrices=False)[2][0]
        if np.dot(d_,mu-[p1['pivotX'],p1['pivotY']])<0: d_=-d_
        d[f]=float(np.degrees(np.arctan2(d_[1],d_[0])))
    return d
if __name__=='__main__':
    for spec in sys.argv[1:]:
        if spec.startswith('ours:'):
            _,v,s=spec.split(':'); d=ours(v,s); print(v,s,{k:round(x,1) for k,x in d.items()},'thumb-index',round(abs(d['Thumb']-d['Index']),1),'index-pinky',round(abs(d['Index']-d['Pinky']),1),'adj',[round(abs(d[a]-d[b]),1) for a,b in (('Index','Middle'),('Middle','Ring'),('Ring','Pinky'))]); continue
        c,s,a,b=spec.split(':'); print(c,'img'+('L' if s=='A' else 'R'),clip(c,s,int(a),int(b)),flush=True)
