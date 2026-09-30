import json,numpy as np
from PIL import Image
H=json.load(open('body_tools/work/apose_turn/angle_map.json'))['handoff']
out={}
for v in ['apose','left','right']:
    h=H[v]; s=h['scale']
    fr=Image.open(f"reference/apose_turn/frames/f{h['frame']:03d}.png").convert('RGB')
    # affine: base = s*frame + d  -> frame = (base-d)/s
    W=fr.transform((1365,1739),Image.AFFINE,(1/s,0,-h['dx']/s,0,1/s,-h['dy']/s),resample=Image.BICUBIC)
    W.save(f'mouth/work/turn_handoff/{v}_warped.png')
    b=np.asarray(Image.open(f'views/{v}/base.png').convert('RGB'),float).mean(2)
    w=np.asarray(W,float).mean(2)
    bb=json.load(open(f'views/{v}/mouth/rig.json'))['drawnMouthBBox']
    m=12; y0,y1,x0,x1=bb['y0']-m,bb['y1']+m+1,bb['x0']-m,bb['x1']+m+1
    t=b[y0:y1,x0:x1]; t=(t-t.mean())/(t.std()+1e-6)
    best=(-9,0,0)
    for dy in range(-30,31):
        for dx in range(-30,31):
            c=w[y0+dy:y1+dy,x0+dx:x1+dx]; c=(c-c.mean())/(c.std()+1e-6)
            sc=(t*c).mean()
            if sc>best[0]: best=(sc,dx,dy)
    out[v]={'frame':h['frame'],'mouth_dx':best[1],'mouth_dy':best[2],'ncc':round(best[0],3)}
    # crop sheet
    cx,cy=(bb['x0']+bb['x1'])//2,(bb['y0']+bb['y1'])//2
    box=(cx-40,cy-40,cx+40,cy+40)
    a=Image.open(f'views/{v}/base.png').convert('RGB').crop(box).resize((320,320),Image.NEAREST)
    c=W.crop(box).resize((320,320),Image.NEAREST)
    sh=Image.new('RGB',(650,320),'white');sh.paste(a,(0,0));sh.paste(c,(330,0));sh.save(f'mouth/work/turn_handoff/{v}_crop.png')
print(json.dumps(out,indent=1))
json.dump(out,open('mouth/work/turn_handoff/offsets.json','w'),indent=1)
