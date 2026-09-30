import cv2,numpy as np,json
V='/workspace/shadowveil/views/'
def ld(p): return cv2.imread(p,cv2.IMREAD_UNCHANGED).astype(np.float32)/255.
def over(dst,src):
    a=src[...,3:4]; out=dst.copy()
    out[...,:3]=src[...,:3]*a+dst[...,:3]*(1-a); out[...,3:4]=a+dst[...,3:4]*(1-a); return out
def expected(view,k,rest,dx=0,dy=0,box=None):
    rig=json.load(open(V+f'{view}/eyes/rig.json'))
    x0,y0,x1,y1=box; E=rest[y0:y1,x0:x1].copy()
    for e in rig['eyes']:
        w=ld(V+f'{view}/eyes/{e}_white.png')[y0:y1,x0:x1]; ir=ld(V+f'{view}/eyes/{e}_iris.png')
        ir=np.roll(ir,(dy,dx),(0,1))[y0:y1,x0:x1]
        lay=w.copy(); a=ir[...,3:4]*w[...,3:4]  # source-atop
        lay[...,:3]=ir[...,:3]*a+w[...,:3]*(1-a)
        E=over(E,lay); E=over(E,ld(V+f'{view}/eyes/{e}_lid_{k}.png')[y0:y1,x0:x1]); E=over(E,ld(V+f'{view}/eyes/{e}_lash.png')[y0:y1,x0:x1])
    return E
if __name__=='__main__':
    for v in ('apose','tpose','left','right'):
        rest=ld(f'/workspace/shadowveil/rig/previews/idle/frames/{v}/rest.png')
        box=json.load(open(V+f'{v}/eyes/rig.json'))['workRegion']; box=[box[0],box[1],box[2]+1,box[3]+1]
        E=expected(v,0,rest,box=box); d=np.abs(E-rest[box[1]:box[3],box[0]:box[2]]).max()*255
        print(v,'expected lid0 vs rest max diff',round(float(d),2))
