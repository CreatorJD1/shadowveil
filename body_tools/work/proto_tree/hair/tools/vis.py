import sys,glob,colorsys; from render import *
def forb(v):
    f_=np.zeros((1739,1365),bool)
    for f in glob.glob(f'{R}/views/{v}/eyes/Eye*_*.png')+glob.glob(f'{R}/views/{v}/mouth/*.png'):
        if 'chroma' in f: continue
        f_|=np.array(Image.open(f).convert('RGBA'))[...,3]>0
    return ndi.binary_dilation(f_,iterations=2)
def vis(v,box,scale,out,hd=None):
    hd=hd or f'{R}/views/{v}/hair'; parts,_=load_rig(v,hd)
    base=np.array(Image.open(f'{R}/views/{v}/base.png').convert('RGBA')).astype(float)
    rgb=np.where(base[...,3:]>0,base[...,:3],255)*0.45+255*0.55
    F=forb(v); rgb[F]=rgb[F]*0.5+np.array([255,0,0])*0.5
    ss=[p for p in parts if p['id'] not in('hair_back','hair_front')]
    for i,p in enumerate(ss):
        a=np.array(Image.open(f"{hd}/{p['file']}"))[...,3]
        c=np.array(colorsys.hsv_to_rgb((i*0.37)%1,0.9,0.9))*255
        m=a>0; rgb[m]=rgb[m]*0.3+c*0.7
        m2=a==255; rgb[m2]=rgb[m2]*0.6+c*0.4*0.5
    x0,y0,x1,y1=box; im=Image.fromarray(rgb[y0:y1,x0:x1].astype(np.uint8)).resize(((x1-x0)*scale,(y1-y0)*scale),Image.NEAREST)
    from PIL import ImageDraw; d=ImageDraw.Draw(im)
    for p in ss:
        x,y=(p['pivotX']-x0+.5)*scale,(p['pivotY']-y0+.5)*scale; d.ellipse([x-4,y-4,x+4,y+4],outline=(0,0,0),width=2)
        d.text((x+5,y-5),p['id'].replace('strand_','s'),fill=(0,0,0))
    im.save(out)
if __name__=='__main__':
    v=sys.argv[1]; box=tuple(map(int,sys.argv[2].split(','))); vis(v,box,int(sys.argv[3]),sys.argv[4],sys.argv[5] if len(sys.argv)>5 else None)
