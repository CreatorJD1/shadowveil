# zoomed crop sheet: source frame | v1 | v2 | v3 hair composited over the source frame with its blue hair key greyed out; row 2 adds the eye-opening outline (magenta) and px restored in v3 (cyan)
from common import *
from PIL import ImageDraw
CR={'045':(568,622,188,236),'315':(738,796,188,246)}; Z=8; rows=[]
for ang,(x0,x1,y0,y1) in CR.items():
    sv=src_view(ang).astype(float); key=np.array(Image.open(f'../{ang}/src_hair_key_view.png'))>0
    bg=sv[...,:3].copy(); bg[key]=[90,90,90]
    op=opening(ang); e=op&~(np.roll(op,1,0)&np.roll(op,-1,0)&np.roll(op,1,1)&np.roll(op,-1,1))
    v2=np.zeros((H,W),bool); v3=np.zeros((H,W),bool)
    for f in glob.glob(f'{R}/hair/staged/diagonals_v2/{ang}/hair/*.png'): v2|=A(f)[...,3]>0
    for f in glob.glob(f'../{ang}/hair/*.png'): v3|=A(f)[...,3]>0
    rest=v3&~v2
    def comp(d):
        c=bg.copy()
        for f in sorted(glob.glob(f'{R}/hair/staged/{d}/{ang}/hair/*.png')):
            a=A(f); m=a[...,3:]/255.; c=c*(1-m)+a[...,:3]*m
        return c
    T=[sv[...,:3],comp('diagonals'),comp('diagonals_v2'),comp('diagonals_v3')]
    for k in (0,1):
        row=[]
        for i,t in enumerate(T):
            t=t.copy()
            if k: t[e]=[255,0,255]; 
            if k and i==3: t[rest]=[0,255,255]
            row.append(t[y0:y1,x0:x1]); row.append(np.full((y1-y0,1,3),255.))
        rows.append(np.concatenate(row,1))
w=max(r.shape[1] for r in rows); rows=[np.pad(r,((0,1),(0,w-r.shape[1]),(0,0)),constant_values=255) for r in rows]
im=Image.fromarray(np.concatenate(rows,0).astype(np.uint8)); im=im.resize((im.width*Z,im.height*Z),Image.NEAREST)
c=Image.new('RGB',(im.width,im.height+30),'white'); c.paste(im,(0,30)); d=ImageDraw.Draw(c)
for i,l in enumerate(['source frame (f033 / f191)','v1 diagonals','v2','v3']): d.text((i*(im.width//4)+6,8),l,fill='black')
d.text((im.width-420,8),'rows: 045, 045+outline, 315, 315+outline | magenta=eye opening, cyan=v3 restored',fill='black')
c.save('../eye_crops_v1_v2_v3_source.png'); print(c.size)
