import numpy as np, json, sys
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import skeletonize
from post import ANG, palette, load_fig, fit, W, H, ROOT
FRAME={'045':'f033','135':'f087','225':'f131','315':'f191'}
GEO=json.load(open('inputs/collage_geometry.json'))
def frame_to_base(fx,fy,ang,fitinfo,gen_size):
    g=GEO[FRAME[ang]]; cx=800+fx*g['s']; cy=(fy-g['y0'])*g['s']
    gx=cx*gen_size[0]/g['collage_w']; gy=cy*gen_size[1]/g['collage_h']
    s=fitinfo['scale']; return s*(gx-fitinfo['src_cx'])+fitinfo['cx_t'], s*(gy-fitinfo['src_top'])+40
def eyes_layer(ang,fitinfo,gen_size,dxy=(0,0)):
    d=f'{ROOT}/eyes/staged/diagonals/{ang}/'
    comp=np.zeros((1168,768,4),np.uint8)
    for e in ('EyeR','EyeL'):
        wt=np.array(Image.open(d+f'{e}_white.png').convert('RGBA')); ir=np.array(Image.open(d+f'{e}_iris.png').convert('RGBA'))
        ld=np.array(Image.open(d+f'{e}_lid_0.png').convert('RGBA')); ls=np.array(Image.open(d+f'{e}_lash.png').convert('RGBA'))
        for L,clip in ((wt,None),(ir,wt[...,3]>0),(ld,None),(ls,None)):
            m=L[...,3]>127
            if clip is not None: m&=clip
            comp[m]=L[m]; comp[m,3]=255
    # inverse map base->frame (nearest) so her exact eye tones survive
    g=GEO[FRAME[ang]]; s=fitinfo['scale']
    yy,xx=np.mgrid[0:H,0:W].astype(float); xx-=dxy[0]; yy-=dxy[1]
    gx=(xx-fitinfo['cx_t'])/s+fitinfo['src_cx']; gy=(yy-40)/s+fitinfo['src_top']
    cx=gx*g['collage_w']/gen_size[0]; cy=gy*g['collage_h']/gen_size[1]
    fx=np.rint((cx-800)/g['s']).astype(int); fy=np.rint(cy/g['s']+g['y0']).astype(int)
    ok=(fx>=0)&(fx<768)&(fy>=0)&(fy<1168)
    out=np.zeros((H,W,4),np.uint8); out[ok]=comp[fy[ok],fx[ok]]
    return out
def run(ang,gen,outp,dxy=(0,0)):
    cfg=ANG[ang]; P=palette(cfg['nb']); rear=ang in('135','225')
    im,keep,bg=load_fig(gen); gsz=(im.shape[1],im.shape[0])
    rgb,m,fi=fit(im,keep,cfg['foot'],cfg['cx'])
    L=rgb.mean(-1); r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]; yy=np.mgrid[0:H,0:W][0]
    tor=m&(yy>560)&(yy<640); sk_L=np.median(L[tor&(L>np.percentile(L[tor],40))]); dark=m&(L<0.55*sk_L)
    mass=nd.binary_opening(dark,structure=np.ones((7,7))); mass=nd.binary_dilation(mass,iterations=1)&dark
    # hair = mass components touching the head top region; other head-zone masses = facial marks/mouth
    lab,n=nd.label(mass); hair_ids=set(np.unique(lab[(yy<200)&mass]))-{0}
    hairm=np.isin(lab,list(hair_ids))&(yy<420)
    clothm=mass&(yy>=330)&~hairm
    facemass=mass&~hairm&~clothm
    eyes=None; eyebox=np.zeros((H,W),bool)
    if not rear:
        eyes=eyes_layer(ang,fi,gsz,dxy); ea=eyes[...,3]>0
        ys,xs=np.nonzero(ea); eyebox[ys.min()-14:ys.max()+6, xs.min()-8:xs.max()+8]=True
    face_y=(yy>200)&(yy<330)
    lip=np.zeros((H,W),bool)
    if not rear:
        cand=m&face_y&(r-b>30)&(L<0.8*sk_L)&~eyebox&~hairm
        cand|=facemass&face_y&(yy>270)
        lab2,n2=nd.label(nd.binary_closing(cand,iterations=2))
        if n2:
            sz=nd.sum(cand,lab2,range(1,n2+1)); lip=(lab2==sz.argmax()+1)&m
    stroke=dark&~mass
    out=np.zeros((H,W,4),np.uint8)
    def put(mk,c): out[mk,:3]=c; out[mk,3]=255
    put(m,P['skin']); put(hairm,P['hair']); put(clothm,P['cloth']); put(lip,P['lip'])
    sk=skeletonize(nd.binary_closing(stroke,iterations=1))&m&~eyebox&~lip
    edge=m&~nd.binary_erosion(m)
    reg=hairm|clothm|lip; medge=reg&~nd.binary_erosion(reg)
    put(sk|edge|medge,P['line'])
    # facial marks the generator invented (dark blobs on the cheeks) are dropped: her marks come with the eye/face parts only
    if eyes is not None:
        out[eyebox&m&~hairm,:3]=P['skin']
        ea=eyes[...,3]>0; out[ea]=eyes[ea]
    Image.fromarray(out).save(outp)
    Image.fromarray(rgb.astype(np.uint8)).save(outp.replace('.png','_upscaled_raw.png'))
    info=dict(angle=ang,gen=gen,palette=P,fit=fi,eye_offset=dxy,rear=rear,lip_px=int(lip.sum()),hair_px=int(hairm.sum()),skin_L=float(sk_L))
    json.dump(info,open(outp.replace('.png','_post.json'),'w'),indent=1); return info
if __name__=='__main__':
    a=sys.argv; dxy=(float(a[4]),float(a[5])) if len(a)>5 else (0,0)
    print(run(a[1],a[2],a[3],dxy))
