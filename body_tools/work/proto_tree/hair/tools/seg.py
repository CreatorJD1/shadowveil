import numpy as np, json, warnings; warnings.filterwarnings('ignore')
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import disk, opening, dilation
VIEWS=['apose','tpose','left','right','back']
# face-feature exclusion boxes (x0,x1,y0,y1), half-open; bun ellipse (cx,cy,ax,ay); ycut = shoulder line
CFG=json.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'cfg.json')))
def load(v): return np.array(Image.open(f'/workspace/shadowveil/views/{v}/base.png').convert('RGBA')).astype(int)
def masks(v):
    c=CFG[v]; im=load(v)
    r,g,b,a=[im[...,i] for i in range(4)]
    lum=(r*299+g*587+b*114)//1000; sat=im[...,:3].max(-1)-im[...,:3].min(-1)
    blue=(a>60)&(b>r+25)&(b>g+25)&(lum<150)
    hair=(a>60)&(((lum<80)&(sat<45))|blue)
    hair[c['ycut']:]=False
    face=np.zeros_like(hair)
    for x0,x1,y0,y1 in c['ex']: face[y0:y1,x0:x1]=True
    hair&=~face
    core=opening(hair,disk(1))
    lab,k=ndi.label(core,structure=np.ones((3,3))); s=ndi.sum(core,lab,range(1,k+1))
    core=np.isin(lab,[i+1 for i,v_ in enumerate(s) if v_>=30])
    keep=dilation(core,disk(1))&hair
    thick=opening(keep,disk(4)); l2,k2=ndi.label(thick); s2=ndi.sum(thick,l2,range(1,k2+1))
    thick=np.isin(l2,[i+1 for i,v_ in enumerate(s2) if v_>=c.get('thickmin',400)])
    thick=keep&dilation(thick,disk(1))  # regrow opening edge within keep
    thin=keep&~thick
    lt,kt=ndi.label(thin,structure=np.ones((3,3))); st=ndi.sum(thin,lt,range(1,kt+1))
    thin=np.isin(lt,[i+1 for i,v_ in enumerate(st) if v_>=30])
    H,W=hair.shape; yy,xx=np.mgrid[:H,:W]
    cx,cy,ax,ay=c['bun']
    bunreg=((xx-cx)/ax)**2+((yy-cy)/ay)**2<1
    return dict(im=im,a=a,blue=blue,hair=hair,keep=keep,thick=thick,thin=thin,bunreg=bunreg,face=face)
