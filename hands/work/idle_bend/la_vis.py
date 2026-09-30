import sys,numpy as np
from PIL import Image,ImageDraw
sys.argv_=sys.argv
import importlib.util
D,view,RIG,S,cns,cx,cy,h,sc,out=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5].split(','),int(sys.argv[6]),int(sys.argv[7]),int(sys.argv[8]),int(sys.argv[9]),sys.argv[10]
sys.argv=['x',D,view,RIG,'/dev/null']
src=open('lineart.py').read().split('res={}')[0];g={};exec(src,g)
from scipy import ndimage as nd
tiles=[]
for cn in cns:
    im=g['comp_dir'](D,cn,S);A=im[...,3];op=A>=128;L=g['line_mask'](im)
    edge=op&~nd.binary_erosion(op,border_value=0);unc=edge&~nd.binary_dilation(L,structure=np.ones((3,3)))
    bg=np.zeros_like(im);bg[...,:3]=200;bg[...,3]=255;c=np.array(Image.alpha_composite(Image.fromarray(bg),Image.fromarray(im)))
    c[unc]=(0,160,255,255)
    t=Image.fromarray(c[cy-h:cy+h,cx-h:cx+h]).resize((2*h*sc,2*h*sc),Image.NEAREST);d=ImageDraw.Draw(t)
    for px,py,ang in g['sharp_pts'](op):
        if abs(px-cx)<h and abs(py-cy)<h: X,Y=(px-cx+h)*sc,(py-cy+h)*sc;d.ellipse([X-5,Y-5,X+5,Y+5],outline=(255,0,0),width=2);d.text((X+6,Y-6),f'{ang:.0f}',fill=(255,0,0))
    for pid,(x,y) in g['joints'](cn,S).items():
        X,Y=(x-cx+h)*sc,(y-cy+h)*sc;d.ellipse([X-2,Y-2,X+2,Y+2],fill=(0,200,0))
    d.text((3,3),cn,fill=(0,0,0));tiles.append(t)
W=2*h*sc;sh=Image.new('RGB',(W*len(tiles),W),'white')
for i,t in enumerate(tiles): sh.paste(t,(i*W,0))
sh.save(out);print(out)
