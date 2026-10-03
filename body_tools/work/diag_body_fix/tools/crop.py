import sys; sys.path.insert(0,'.'); from posekit import *
from PIL import ImageDraw
def crop(ang,x0,y0,x1,y1,z,name,pts=()):
    F=frame(ang).astype(np.uint8); c=Image.fromarray(F[y0:y1,x0:x1]).resize(((x1-x0)*z,(y1-y0)*z),Image.NEAREST); d=ImageDraw.Draw(c)
    for x in range(x0-x0%10+10,x1,10):
        d.line([((x-x0)*z,0),((x-x0)*z,(y1-y0)*z)],fill=(255,255,255) if x%50==0 else (120,120,200))
        d.text(((x-x0)*z+2,2),str(x),fill=(255,255,0))
    for y in range(y0-y0%10+10,y1,10):
        d.line([(0,(y-y0)*z),((x1-x0)*z,(y-y0)*z)],fill=(255,255,255) if y%50==0 else (120,120,200))
        d.text((2,(y-y0)*z+2),str(y),fill=(255,255,0))
    for px,py,col in pts: d.ellipse([(px-x0)*z-5,(py-y0)*z-5,(px-x0)*z+5,(py-y0)*z+5],outline=col,width=2)
    c.save(f'/workspace/shadowveil/body_tools/work/diag_body_fix/tools/_{name}.png')
if __name__=='__main__':
    a=sys.argv; pts=[(float(a[i]),float(a[i+1]),(255,0,0)) for i in range(8,len(a),2)]; crop(a[1],*map(int,a[2:7]),a[7],pts)
