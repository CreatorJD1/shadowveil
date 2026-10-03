# Crop sheet: rig (headgroup=1, rest) vs turn frame, per handoff eye; outlines + overlay at 0 and at the measured residual.
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage as ndi
Q='/workspace/shadowveil/eyes/qa/headgroup_handoff/'
vis=np.load(Q+'work/vis.npy',allow_pickle=True).item();rep=json.load(open(Q+'report.json'))
Z=6
try:F1=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15);F2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',17)
except Exception:F1=F2=ImageFont.load_default()
def edge(m):return m&~ndi.binary_erosion(m)
def tile(img,box,marks):
    x0,y0,x1,y1=box;c=img[y0:y1,x0:x1].astype(float).copy()
    for m,col in marks:
        e=edge(m)[y0:y1,x0:x1];c[e]=col
    return Image.fromarray(c.clip(0,255).astype(np.uint8)).resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST)
rows=[]
for k,d in vis.items():
    r=rep['eyes'][k];bx,by=r['best_estimate_residual'];bxi,byi=int(round(bx)),int(round(by))
    oR,oF=d['oR'],d['oF'];ys,xs=np.nonzero(oR['band']|oF['band'])
    box=(xs.min()-14,ys.min()-14,xs.max()+15,ys.max()+26)
    RG,F=d['RG'],d['F']
    sh=lambda m:ndi.shift(m,(byi,bxi),order=0)
    t1=tile(RG,box,[(oR['band'],(255,0,255)),(oR['iris'],(0,255,255))])
    t2=tile(F,box,[(oF['band'],(255,255,0)),(oF['iris'],(0,255,0))])
    gF=(F.mean(2,keepdims=True)*np.ones(3)*0.8+40)
    blend0=0.5*RG+0.5*F
    t3=tile(blend0,box,[(oR['band'],(255,0,255)),(oR['iris'],(0,255,255)),(oF['band'],(255,255,0)),(oF['iris'],(0,255,0))])
    RGs=np.stack([ndi.shift(RG[...,i].astype(float),(byi,bxi),order=0,mode='nearest') for i in range(3)],-1)
    t4=tile(0.5*RGs+0.5*F,box,[(sh(oR['band']),(255,0,255)),(sh(oR['iris']),(0,255,255)),(oF['band'],(255,255,0)),(oF['iris'],(0,255,0))])
    rows.append((k,r,[t1,t2,t3,t4],(bxi,byi)))
W=sum(t.width for t in rows[0][2])+3*8+20;H=sum(t[2][0].height+70 for t in rows)+130
S=Image.new('RGB',(max(W,1200),H),(24,24,28));D=ImageDraw.Draw(S)
D.text((10,8),'Eye handoff offsets with head group (?headgroup=1, rest) - Base Eyes, Oct 2 2026 PT. Residual = turn frame minus rig, view px (+x right, +y down).',font=F2,fill=(255,255,255))
D.text((10,32),'Columns: rig render | turn frame (warped with Body angle_map handoff) | 50/50 blend at 0 | 50/50 blend after shifting the rig by the best-estimate residual.',font=F1,fill=(210,210,210))
D.text((10,52),'Outlines: magenta = rig lash band, cyan = rig iris, yellow = frame lash band, green = frame iris. Zoom x6.',font=F1,fill=(210,210,210))
y=85
for k,r,ts,(bxi,byi) in rows:
    m=r['methods'];D.text((10,y),f"{k}  ({r['frame']}, view '{r['view']}', head offset {tuple(r['headgroup_offset'])})   best residual ({r['best_estimate_residual'][0]:+.1f}, {r['best_estimate_residual'][1]:+.1f})   iris ({m['iris_opening_centroid'][0]:+.1f}, {m['iris_opening_centroid'][1]:+.1f})   lash band ({m['lash_band_centroid'][0]:+.1f}, {m['lash_band_centroid'][1]:+.1f})   lash chamfer ({m['upper_lash_chamfer'][0]:+d}, {m['upper_lash_chamfer'][1]:+d})   mouth face residual {tuple(r['mouth_face_residual'])}",font=F1,fill=(255,230,150))
    x=10;y+=24
    for t,lab in zip(ts,['rig','frame','blend @0',f'blend @({bxi:+d},{byi:+d})']):
        S.paste(t,(x,y));D.text((x+4,y+4),lab,font=F1,fill=(255,255,255));x+=t.width+8
    y+=ts[0].height+40
S.save(Q+'sheet.png');print(S.size)
