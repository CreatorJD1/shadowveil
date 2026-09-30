from PIL import Image
import numpy as np
from scipy import ndimage as ndi
a=np.array(Image.open('front.png').convert('RGBA')).astype(float)
X0,Y0,X1,Y1=640,266,722,310
reg=a[Y0:Y1,X0:X1,:3]
lum=reg@[0.299,0.587,0.114]
# skin sample: ring around mouth
skin=np.median(a[270:278,665:700,:3].reshape(-1,3),0); print('skin median',skin, np.std(a[270:278,665:700,:3].reshape(-1,3),0))
sl=skin@[0.299,0.587,0.114]
dark=lum<sl-35
lab,n=ndi.label(dark); sizes=ndi.sum(dark,lab,range(1,n+1)); print('comps',sizes)
m=lab==(np.argmax(sizes)+1)
m=ndi.binary_fill_holes(ndi.binary_closing(m,iterations=2))
ys,xs=np.nonzero(m); print('bbox canvas x',xs.min()+X0,xs.max()+X0,'y',ys.min()+Y0,ys.max()+Y0)
# per-column top/bottom
for x in range(xs.min(),xs.max()+1):
    col=np.nonzero(m[:,x])[0]
    print(x+X0, col.min()+Y0, col.max()+Y0, end=' | ')
print()
px=reg[m]; 
from scipy.cluster.vq import kmeans2
np.random.seed(0)
c,l=kmeans2(px,6,minit='++',seed=1)
for i in np.argsort(c@[0.299,0.587,0.114]): print('%02x%02x%02x'%tuple(c[i].astype(int)),(l==i).sum())
np.save('mask.npy',m)
