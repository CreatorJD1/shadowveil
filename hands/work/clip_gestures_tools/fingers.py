import sys,json,numpy as np,cv2
sys.path.insert(0,'/workspace/gb'); from tracks import track
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
def fgmask(im): 
    im=im.astype(int); return ~((im[...,2]>120)&(im[...,2]>im[...,0]+60)&(im[...,2]>im[...,1]+60))
def analyse(im,cx,cy,wr,S=80,r_open=None):
    x0,y0=int(cx-S),int(cy-S); cr=im[y0:y0+2*S,x0:x0+2*S]; m=fgmask(cr)
    # keep component containing the centre
    lab,n=ndi.label(m); c=lab[S,S] if lab[S,S] else np.bincount(lab.ravel())[1:].argmax()+1; m=lab==c
    dt=ndi.distance_transform_edt(m); pr=dt.max()   # palm radius ~ max inscribed
    ro=r_open or max(4,int(pr*0.55))
    yy,xx=np.mgrid[-ro:ro+1,-ro:ro+1]; disk=xx**2+yy**2<=ro*ro
    palm=ndi.binary_opening(m,disk); fing=m&~ndi.binary_dilation(palm,iterations=1)
    lab2,n2=ndi.label(fing); comps=[]
    pcy,pcx=np.unravel_index(dt.argmax(),dt.shape)
    for k in range(1,n2+1):
        ys,xs=np.nonzero(lab2==k)
        if len(ys)<25: continue
        P=np.stack([xs,ys],1).astype(float); mu=P.mean(0); U,s_,Vt=np.linalg.svd(P-mu,full_matrices=False); d=Vt[0]
        if np.dot(d,mu-[pcx,pcy])<0: d=-d
        L=np.ptp((P-mu)@d); Wd=np.ptp((P-mu)@Vt[1])
        if L<1.6*Wd: continue
        comps.append(dict(ang=float(np.degrees(np.arctan2(d[1],d[0]))),len=float(L),wid=float(Wd),mu=(mu+[x0,y0]).tolist(),area=int(len(ys))))
    return dict(comps=sorted(comps,key=lambda c:c['ang']),palm_r=float(pr),palm_c=(pcx+x0,pcy+y0),mask=m,fing=fing,x0=x0,y0=y0)
if __name__=='__main__':
    c=sys.argv[1]; side=sys.argv[2]; frs=[int(x) for x in sys.argv[3].split(',')]
    tr,F=track(c); t=tr[side]; tiles=[]
    for i in frs:
        r=analyse(F[i],t['x'][i],t['y'][i],None)
        print(c,side,i,'palm_r',round(r['palm_r'],1),[(round(q['ang']),round(q['len']),round(q['wid'])) for q in r['comps']])
        im=Image.fromarray(F[i]).crop((r['x0'],r['y0'],r['x0']+160,r['y0']+160)).resize((320,320),Image.NEAREST); d=ImageDraw.Draw(im)
        a=np.array(im); fm=np.kron(r['fing'],np.ones((2,2),bool)); a[fm]=(a[fm]*0.5+[0,255,0]).clip(0,255).astype(np.uint8); im=Image.fromarray(a); d=ImageDraw.Draw(im)
        for q in r['comps']:
            mx,my=(q['mu'][0]-r['x0'])*2,(q['mu'][1]-r['y0'])*2; th=np.radians(q['ang']); d.line([(mx-np.cos(th)*q['len'],my-np.sin(th)*q['len']),(mx+np.cos(th)*q['len'],my+np.sin(th)*q['len'])],fill='red',width=2); d.text((mx,my),f"{q['ang']:.0f}",fill='white')
        d.text((3,3),f'{c} {i}',fill='white'); tiles.append(im)
    o=Image.new('RGB',(320*len(tiles),320))
    for k,tl in enumerate(tiles): o.paste(tl,(320*k,0))
    o.save(sys.argv[4])
