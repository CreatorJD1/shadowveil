# Opening-based iris segmentation (same rule for rig render and turn frame).
import numpy as np
from scipy import ndimage as ndi
def seg(I,lab,bgm,win,E,ref):
    x0,y0,x1,y1=win;L,a,b=lab(I);bg=bgm(I);C=np.hypot(a,b)
    W=np.zeros(L.shape,bool);W[y0:y1,x0:x1]=True
    blk=W&(L<14)&~bg
    lb,n=ndi.label(blk);best=None
    for k in range(1,n+1):
        ys,xs=np.nonzero(lb==k);w=np.ptp(xs)+1
        if w<14:continue
        # thickness: median rows per column
        th=np.median([np.sum(xs==x) for x in np.unique(xs)])
        sc=w*min(th,6)/(1+np.hypot(xs.mean()-ref[0],ys.mean()-ref[1])/6)
        if best is None or sc>best[0]:best=(sc,k)
    band=lb==best[1];bys,bxs=np.nonzero(band)
    skin=W&~bg&(L>45)&(L<80)&(a>8)&(b>15);sL,sa,sb=[np.median(q[skin]) for q in (L,a,b)]
    dE=np.sqrt((L-sL)**2+(a-sa)**2+(b-sb)**2);white=(L>72)&(C<16)
    roi=np.zeros_like(W);xs_=np.unique(bxs)
    for x in xs_[1:-1]:
        yb=bys[bxs==x].max();y=yb+1;seen=False
        while y<yb+16 and y<y1:
            if L[y,x]<30 and seen:break
            if L[y,x]>=30:seen=True
            if seen and dE[y,x]<9 and not white[y,x]:  # back to plain skin: below the opening
                break
            roi[y,x]=True;y+=1
    roi&=~bg&(ndi.distance_transform_edt(~bg)>2)
    hue=np.degrees(np.arctan2(b,a));sh=np.degrees(np.arctan2(sb,sa))
    if E=='EyeL': iris=roi&~white&(L>=25)&(a<sa-10)
    else:         iris=roi&~white&(L>=25)&(hue>sh+5)&(C>6)
    pupil=roi&(L<25)&ndi.binary_dilation(iris,iterations=2)
    iris=ndi.binary_fill_holes(iris|pupil)&roi
    lab_,n2=ndi.label(iris)
    if n2>1:
        sz=ndi.sum(iris,lab_,range(1,n2+1));iris=np.isin(lab_,1+np.nonzero(np.array(sz)>=4)[0])
    open_=roi&(white|iris|(L<30))
    return dict(band=band,roi=roi,iris=iris,opening=open_,skin=(sL,sa,sb))
