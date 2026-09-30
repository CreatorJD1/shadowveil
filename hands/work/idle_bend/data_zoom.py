# knuckle zoom sheet: data_zoom.py <out.png> <cx> <cy> <S> <half> <scale> <cases,..> <label=dir> ...   (hand-only composite on grey, new defects outlined red)
import sys,json,numpy as np
from PIL import Image,ImageDraw
sys.argv=[a for a in sys.argv]
out,cx,cy,S,h,sc=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],int(sys.argv[5]),int(sys.argv[6]);cases=sys.argv[7].split(',');runs=[a.split('=') for a in sys.argv[8:]]
from pivot_qa_lib import comp_dir,masks,disk
from scipy import ndimage as nd
tiles=[]
for lab,D in runs:
    row=[]
    R0=comp_dir(D,'rest',S)[...,3];re,rt,rs=masks(R0)
    for cn in cases:
        im=comp_dir(D,cn,S);A=im[...,3];e,t,s=masks(A)
        bad=(e&~nd.binary_dilation(re,structure=disk(3)))|(t&~nd.binary_dilation(rt,structure=disk(3)))|(s&~nd.binary_dilation(rs,structure=disk(2)))
        bg=np.zeros_like(im);bg[...,:3]=(200,200,200);bg[...,3]=255
        c=Image.alpha_composite(Image.fromarray(bg),Image.fromarray(im));c=np.array(c);c[bad]=(255,0,0,255)
        crop=Image.fromarray(c[cy-h:cy+h,cx-h:cx+h]).resize((2*h*sc,2*h*sc),Image.NEAREST)
        d=ImageDraw.Draw(crop);d.text((3,3),f'{lab} {cn}',fill=(0,0,0));row.append(crop)
    tiles.append(row)
W=2*h*sc;sheet=Image.new('RGB',(W*len(cases),W*len(runs)),'white')
for i,row in enumerate(tiles):
    for k,t in enumerate(row): sheet.paste(t,(k*W,i*W))
sheet.save(out);print(out,sheet.size)
