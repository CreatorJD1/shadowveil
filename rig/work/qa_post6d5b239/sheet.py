import numpy as np
from PIL import Image, ImageDraw
V=['apose','tpose','left','right','back'];D=[45,90,135,-45]
rows=[]
for v in V:
    r=np.array(Image.open(f'rest_{v}.png')); ims=[Image.open(f'rest_{v}.png')]+[Image.open(f'turned_{v}_{d}.png') for d in D]
    m=np.zeros(r.shape[:2],bool)
    T=[np.array(im).astype(int) for im in ims[1:]]
    for i in range(len(T)):
        for j in range(i+1,len(T)): m|=(np.abs(T[i]-T[j]).max(-1)>40)
    ys,xs=np.nonzero(m)
    # split into left/right halves of the canvas to get two hand crops
    crops=[]
    for sel in [xs<r.shape[1]//2, xs>=r.shape[1]//2]:
        if sel.sum()<200: continue
        x0,x1,y0,y1=xs[sel].min()-40,xs[sel].max()+40,ys[sel].min()-40,ys[sel].max()+40
        crops.append((max(0,x0),max(0,y0),x1,y1))
    for c in crops:
        tiles=[im.crop(c) for im in ims]; h=260; tiles=[t.resize((max(1,int(t.width*h/t.height)),h)) for t in tiles]
        row=Image.new('RGB',(sum(t.width for t in tiles)+10*len(tiles)+120,h+20),'white'); d=ImageDraw.Draw(row); d.text((4,4),f'{v}\n'+','.join(map(str,map(int,c))),fill='black'); x=120
        for t,lab in zip(tiles,['rest']+[f'{a}deg' for a in D]):
            row.paste(t,(x,20),t); d.text((x,4),lab,fill='black'); x+=t.width+10
        rows.append(row)
W=max(r.width for r in rows); S=Image.new('RGB',(W,sum(r.height for r in rows)),'white'); y=0
for r in rows: S.paste(r,(0,y)); y+=r.height
S.save('contact_turned_hands.png'); print(S.size)
