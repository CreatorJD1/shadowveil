import sys; import numpy as np; from PIL import Image, ImageDraw
ROOT='/workspace/shadowveil'
def comp(v,n,box,z,bg=(0,0,255)):
    b=Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA'); c=Image.new('RGBA',b.size,bg+(255,)); c.alpha_composite(b)
    if n: c.alpha_composite(Image.open(f'{ROOT}/views/{v}/mouth/{n}.png' if '/' not in n else n).convert('RGBA'))
    return c.crop(box).resize(((box[2]-box[0])*z,(box[3]-box[1])*z),Image.NEAREST).convert('RGB')
if __name__=='__main__':
    v=sys.argv[1]; ax,ay=map(int,sys.argv[2:4]); box=(ax-40,ay-28,ax+40,ay+22); z=6
    ims=[comp(v,n,box,z) for n in ['rest','M','anger']]
    out=Image.new('RGB',(ims[0].width,ims[0].height*3)); [out.paste(im,(0,i*im.height)) for i,im in enumerate(ims)]
    out.save(f'tmp/zoom_{v}.png')
