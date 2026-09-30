"""Task 3: sample 20 clean-room stills (one at a time), measure hair.png extent vs figure; sheet. Reference only."""
import json,os,gc,numpy as np
from PIL import Image,ImageDraw
ROOT='/workspace/shadowveil'; S=ROOT+'/reference/grok_build/public/clean-room/layers/hierarchy/still'; OUT=ROOT+'/hair/qa/export_check'
ids=sorted(os.listdir(S)); pick=[ids[round(i*(len(ids)-1)/19)] for i in range(20)]
def bbox(a):
    ys,xs=np.nonzero(a); return (xs.min(),ys.min(),xs.max(),ys.max()) if len(xs) else None
rows=[];thumbs=[]
for i in pick:
    L=json.load(open(f'{S}/{i}/layers.json')); lay={l['id']:l for l in L['layers']}
    h=Image.open(f'{S}/{i}/hair.png').convert('RGBA'); hb=lay['hair'].get('box'); bbx=lay['body'].get('box')
    a=np.array(h)[...,3]>32; b=bbox(a)
    if b is None: rows.append(dict(id=i,empty=True)); continue
    ox,oy=(hb['x'],hb['y']) if hb and h.size!=tuple(L['size']) else (0,0)
    hx0,hy0,hx1,hy1=b[0]+ox,b[1]+oy,b[2]+ox,b[3]+oy
    fig_h=bbx['h'] if bbx else L['size'][1]; fig_top=bbx['y'] if bbx else 0
    # hanging length: rows of hair below the widest row (skull) ... use fraction of hair pixels below 60% of hair height
    col=a.sum(1); H=b[3]-b[1]+1; below=a[b[1]+int(0.6*H):].sum()/max(a.sum(),1)
    rows.append(dict(id=i,role=lay['hair'].get('role'),hair_h=int(H),hair_w=int(b[2]-b[0]+1),hair_h_over_fig=round(H/fig_h,3),
                     h_over_w=round(H/(b[2]-b[0]+1),2),hair_top_rel=round((hy0-fig_top)/fig_h,3),bottom_frac_px=round(float(below),3),role_note=lay['hair'].get('role')))
    t=h.crop(b); t.thumbnail((120,160)); bg=Image.new('RGB',(120,175),(60,150,60)); bg.paste(t,((120-t.width)//2,0),t)
    ImageDraw.Draw(bg).text((2,162),i[:20],fill=(255,255,0)); thumbs.append(bg)
    del h,a; gc.collect()
# ours
for v in ['apose','tpose','left','right','back']:
    u=None
    for f in os.listdir(f'{ROOT}/views/{v}/hair'):
        if f.endswith('.png'):
            m=np.array(Image.open(f'{ROOT}/views/{v}/hair/{f}'))[...,3]>32; u=m if u is None else u|m
    b=bbox(u); fb=bbox(np.array(Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA'))[...,3]>32)
    H=b[3]-b[1]+1; below=u[b[1]+int(0.6*H):].sum()/u.sum()
    rows.append(dict(id='OURS_'+v,hair_h=int(H),hair_w=int(b[2]-b[0]+1),hair_h_over_fig=round(H/(fb[3]-fb[1]+1),3),h_over_w=round(H/(b[2]-b[0]+1),2),bottom_frac_px=round(float(below),3)))
json.dump(rows,open(OUT+'/stills_survey.json','w'),indent=1)
sheet=Image.new('RGB',(120*10,175*2),(0,0,0))
for k,t in enumerate(thumbs): sheet.paste(t,((k%10)*120,(k//10)*175))
sheet.save(OUT+'/stills_hair_sheet.png')
for r in rows: print({k:r[k] for k in r if k not in('role','role_note')})
