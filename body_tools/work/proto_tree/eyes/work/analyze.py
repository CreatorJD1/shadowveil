import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
EYES={ # view: eye: (bbox x0,y0,x1,y1), seed (x,y)
 'front':{'eyeR':((632,218,672,242),(640,231)),'eyeL':((698,216,745,242),(730,231))},
 'left':{'eyeL':((600,202,640,228),(625,214))},
 'right':{'eyeR':((730,202,770,228),(745,214))},
}
def load(v): return np.array(Image.open(f'src_{v}.png').convert('RGBA')).astype(int)
def classify(a,bb,seed):
    x0,y0,x1,y1=bb; sub=a[y0:y1,x0:x1,:3]
    # skin reference from bbox border
    border=np.concatenate([sub[0],sub[-1],sub[:,0],sub[:,-1]])
    lum=sub.mean(2)
    bl=border.mean(1); skin=np.median(border[(bl>90)&(bl<200)],0)
    d=np.sqrt(((sub-skin)**2).sum(2))
    isskin=d<45
    dark=lum<75
    interior=~isskin & ~dark
    lab,n=ndi.label(interior)
    s=lab[seed[1]-y0,seed[0]-x0]
    return sub,skin,d,lum,isskin,dark,interior,lab
if __name__=='__main__':
    for v,eyes in EYES.items():
        a=load(v)
        for e,(bb,seed) in eyes.items():
            sub,skin,d,lum,isskin,dark,interior,lab=classify(a,bb,seed)
            print(v,e,'skin',skin)
            for y in range(sub.shape[0]):
                print('%3d '%(y+bb[1])+''.join('#' if dark[y,x] else ('.' if isskin[y,x] else ('o')) for x in range(sub.shape[1])))
