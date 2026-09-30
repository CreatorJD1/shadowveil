from PIL import Image
import numpy as np
from scipy import ndimage as ndi
def load(v): return np.array(Image.open(f'/workspace/shadowveil/views/{v}/base.png').convert('RGBA')).astype(np.float64)
def lip_mask(b,gx,gy,win=45,profile=False):
    H,W=b.shape[:2]
    x0,y0,x1,y1=gx-win,gy-win,gx+win,gy+win
    reg=b[y0:y1,x0:x1]; rgb=reg[...,:3]; al=reg[...,3]
    lum=rgb@[0.299,0.587,0.114]
    opaque=al>250
    skin=np.median(rgb[opaque&(lum>120)&(lum<200)],0); sl=skin@[0.299,0.587,0.114]
    dark=(lum<sl-35)&(rgb[...,0]>=rgb[...,2])&(al>0)
    if profile: dark=(lum<sl-35)&(rgb[...,0]-rgb[...,2]>18)&(al>0)
    lab,n=ndi.label(dark)
    yy,xx=np.mgrid[0:2*win,0:2*win]
    best=None
    for i in range(1,n+1):
        mk=lab==i; s=mk.sum()
        if s<30: continue
        d=np.hypot(yy[mk].mean()-win,xx[mk].mean()-win)
        sc=s/(1+d/8)
        if best is None or sc>best[0]: best=(sc,i)
    core=lab==best[1]
    # add nearby dark components (corner flicks / seam fragments) within 3px
    near=ndi.binary_dilation(core,iterations=3)
    for i in range(1,n+1):
        if (lab==i).sum()>=1 and (near&(lab==i)).any(): core|=lab==i
    core=ndi.binary_fill_holes(core if profile else ndi.binary_closing(core,iterations=2))
    # drawn-lip pixels: core plus AA pixels around it that are visibly darker than skin
    drawn=core|(ndi.binary_dilation(core,iterations=2)&(lum<sl-10)&(rgb[...,0]>=rgb[...,2])&(al>0))
    M=np.zeros((H,W),bool); M[y0:y1,x0:x1]=core
    D=np.zeros((H,W),bool); D[y0:y1,x0:x1]=drawn
    return M,D,skin
if __name__=='__main__':
    for v,g in {'apose':(681,289),'tpose':(684,281),'left':(609,285),'right':(774,272)}.items():
        b=load(v); M,D,skin=lip_mask(b,*g,profile=v in('left','right'))
        ys,xs=np.nonzero(M); yd,xd=np.nonzero(D)
        print(v,'core bbox',xs.min(),ys.min(),xs.max(),ys.max(),'drawn bbox',xd.min(),yd.min(),xd.max(),yd.max(),'n',M.sum(),D.sum(),'skin','%02x%02x%02x'%tuple(skin.astype(int)))
        np.save(f'lip_{v}.npy',np.stack([M,D]))
