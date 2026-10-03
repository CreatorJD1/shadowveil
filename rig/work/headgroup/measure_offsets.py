# head vs torso offset at each driver handoff: turn frame (placed with angle_map fit) vs live rig, edge-NCC brute force.
import json,numpy as np; from PIL import Image; from scipy import ndimage as nd
D='/workspace/shadowveil/rig/work/qa_post6d5b239/driver_turn'
def edges(f):
    a=np.array(Image.open(f).convert('RGBA')).astype(float); g=a[...,:3].mean(-1)*a[...,3]/255+255*(1-a[...,3]/255)
    return np.hypot(nd.sobel(g,0),nd.sobel(g,1))
def best(A,B,box,R=32):
    x0,y0,x1,y1=box; b=B[y0:y1,x0:x1]; b=(b-b.mean())/(b.std()+1e-9); res=(-9,0,0)
    for dy in range(-R,R+1):
        for dx in range(-R,R+1):
            a=A[y0+dy:y1+dy,x0+dx:x1+dx]; a=(a-a.mean())/(a.std()+1e-9); s=float((a*b).mean())
            if s>res[0]: res=(s,dx,dy)
    return res
BOXV={'apose':{'face':(600,150,765,312),'torso':(540,380,830,560)},'left':{'face':(585,170,705,330),'torso':(560,380,760,560)},'right':{'face':(660,170,780,330),'torso':(600,380,800,560)},'back':{'face':(600,110,760,300),'torso':(560,380,800,560)}}
HO={'apose':1,'left':62,'back':109,'right':160}; out={}
for v,f in HO.items():
    A=edges(f'{D}/handoff_{v}_frame.png'); B=edges(f'{D}/handoff_{v}_live.png'); r={'frame':f}
    for k,bx in BOXV[v].items():
        s,dx,dy=best(A,B,bx); r[k]=dict(dx=dx,dy=dy,ncc=round(s,3))   # frame content = live content shifted by (dx,dy)
    r['head_rel_torso']=dict(dx=r['face']['dx']-r['torso']['dx'],dy=r['face']['dy']-r['torso']['dy'])
    out[v]=r; print(v,r)
json.dump(out,open('handoff_offsets.json','w'),indent=1)
