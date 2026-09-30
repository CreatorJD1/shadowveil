# Contact sheet of worst frames: [video crop | rest crop (base.png on grey, same window) | mask panels]. Nothing drawn on her.
import json,subprocess
from common import *
from PIL import ImageDraw,ImageFont
A=json.load(open(f'{OUT}/data/aggregate.json'))['per_video']
def grab(vid,n,s):
    cmd=['nice','-n','10','ffmpeg','-v','error','-threads','1','-i',vid,'-vf',f'select=eq(n\\,{n}),crop={s.w}:{s.h}:{s.x0}:{s.y0}','-vframes','1','-f','rawvideo','-pix_fmt','rgb24','-']
    b=subprocess.run(cmd,capture_output=True).stdout; return np.frombuffer(b,np.uint8).reshape(s.h,s.w,3).copy()
VIEWS={}
def V(v):
    if v not in VIEWS: VIEWS[v]=View(v)
    return VIEWS[v]
def vidpath(name):
    if name.startswith('keys_'):
        c,v=name[5:].rsplit('_',1); return f'{IDLE}/keys/{c}_{v}.mp4'
    return {'apose_hair_stiff':f'{IDLE}/apose_idle_hair_stiff.mp4','apose_hair_middle':f'{IDLE}/apose_idle_hair_middle.mp4'}.get(name,f'{IDLE}/{name}_idle.mp4')
def meta_frame(name,i):
    m=json.load(open(f'{IDLE}/frames/{name}/meta.json')); return m['frames'][i]
def c1masks(s,img,fm):
    Hm=rotAt(PIV[0],PIV[1],(fm['bones'].get('head') or fm['bones'].get('torso'))[2]); HmR=s.roi_M(Hm)
    Mw=warp(s.Mhead.astype(np.uint8),HmR,s.w,s.h,True)>0; Bw=warp(s.boxmask.astype(np.uint8),HmR,s.w,s.h,True)>0; Sw=warp(s.sil.astype(np.uint8),HmR,s.w,s.h,True)>0
    out={}
    for c_,fn in (('white',cls_white),('blue',cls_blue),('grey',cls_grey)):
        rc=warp(fn(s.base_comp).astype(np.uint8),HmR,s.w,s.h,True); out[c_]=fn(img)&Mw&~Bw&~(cv2.dilate(rc,disk(2))>0)
    return out,Mw,Sw,Bw,HmR,Hm
def hair_front_alpha(s,fm,Hm=None,keys=None):
    Ms=s.hair_M(fm['hair']); a=np.zeros((s.h,s.w),np.float32)
    for k in (keys or s.by):
        M=Ms[k] if Hm is None else Hm@Ms[k]; a=np.maximum(a,warp(s.pa[k],s.roi_M(M),s.w,s.h))
    return a
Z=3; C=64   # crop 64x64 source px shown at 3x
def cropc(a,cx,cy,s):
    x0=int(np.clip(cx-C//2,0,s.w-C)); y0=int(np.clip(cy-C//2,0,s.h-C)); return a[y0:y0+C,x0:x0+C],(x0+s.x0,y0+s.y0)
def up(a): return cv2.resize(a,(C*Z,C*Z),interpolation=cv2.INTER_NEAREST)
def colmask(layers):
    img=np.zeros((C,C,3),np.uint8)
    for m,col in layers: img[m>0]=col
    return img
rows=[]
def add(title,panels):
    rows.append((title,panels))
def row_c1(name,frame,cx=None,cy=None,note=''):
    s=V(A[name]['view'] if 'view' in A[name] else None) if False else V(json.load(open(f'{OUT}/data/{name}.json'))['view'])
    img=grab(vidpath(name),frame,s); fm=meta_frame(name,frame)
    m,Mw,Sw,Bw,HmR,Hm=c1masks(s,img,fm)
    allm=m['white']|m['blue']|m['grey']
    if cx is None:
        ys,xs=np.nonzero(allm); cx,cy=(int(np.median(xs)),int(np.median(ys))) if len(xs) else (s.w//2,s.h//2)
    fr,(ox,oy)=cropc(img,cx,cy,s); re,_=cropc(s.base_comp,cx,cy,s)
    lay=[(cropc(Mw,cx,cy,s)[0],(40,40,40)),(cropc(Sw&Mw,cx,cy,s)[0],(70,70,110)),(cropc(m['grey']&~Sw,cx,cy,s)[0],(0,200,255)),(cropc(m['grey']&Sw,cx,cy,s)[0],(255,0,255)),(cropc(m['white'],cx,cy,s)[0],(255,255,255)),(cropc(m['blue'],cx,cy,s)[0],(0,0,255))]
    ha=hair_front_alpha(s,fm,Hm,[k for k in s.sway if k!='bun']); hr=hair_front_alpha(s,{'hair':{}},None,[k for k in s.sway if k!='bun'])
    lay2=[(cropc(hr>0.5,cx,cy,s)[0],(0,140,0)),(cropc(ha>0.5,cx,cy,s)[0],(220,60,60)),(cropc((ha>0.5)&(hr>0.5),cx,cy,s)[0],(220,200,60))]
    t=fm['t']
    add(f"{name}  f{frame}  t={t:.3f}s (video {frame/30:.3f}s)  window x{ox}-{ox+C} y{oy}-{oy+C}  new white {int((m['white']).sum())} / blue {int(m['blue'].sum())} / bg-inside {int((m['grey']&Sw).sum())} / bg-outside {int((m['grey']&~Sw).sum())} px (whole ROI){note}",
        [('video frame',up(fr)),('rest base.png',up(re)),('check-1 mask',up(colmask(lay))),('strands rest/now',up(colmask(lay2)))])
def row_c2(name,frame,box):
    s=V(json.load(open(f'{OUT}/data/{name}.json'))['view']); img=grab(vidpath(name),frame,s); fm=meta_frame(name,frame)
    Hm=rotAt(PIV[0],PIV[1],(fm['bones'].get('head') or fm['bones'].get('torso'))[2]); HmR=s.roi_M(Hm)
    local=warp(img,np.linalg.inv(HmR),s.w,s.h)
    nh=s.hairlike(local)&~(cv2.dilate(s.hairlike(s.base_comp).astype(np.uint8),disk(1))>0)&s.boxm[box]
    front=[k for k in s.by if s.layers[k]>=600]
    fa=hair_front_alpha(s,fm,None,front); ra=hair_front_alpha(s,{'hair':{}},None,front)
    b=s.boxes[box]; cx,cy=(b[0]+b[2])//2-s.x0,(b[1]+b[3])//2-s.y0
    fr,(ox,oy)=cropc(local,cx,cy,s); re,_=cropc(s.base_comp,cx,cy,s)
    bm=cropc(s.boxm[box],cx,cy,s)[0]; bedge=bm&~(cv2.erode(bm.astype(np.uint8),disk(1))>0)
    lay=[(bedge,(90,90,90)),(cropc(nh,cx,cy,s)[0],(255,160,0))]
    lay2=[(bedge,(90,90,90)),(cropc(ra>0.25,cx,cy,s)[0],(0,140,0)),(cropc((fa>0.25)&(ra<0.25),cx,cy,s)[0],(255,0,0))]
    add(f"{name}  f{frame}  t={fm['t']:.3f}s  {box} box {b}: video hair-coloured new px {int(nh.sum())}, geometric hair-over-box px {int(((fa>0.25)&(ra<0.25)&s.boxm[box]).sum())}  (head-local)",
        [('video (head-local)',up(fr)),('rest base.png',up(re)),('video hair-colour mask',up(colmask(lay))),('geometric hair in box',up(colmask(lay2)))])
def row_bun(name,frame):
    s=V(json.load(open(f'{OUT}/data/{name}.json'))['view']); img=grab(vidpath(name),frame,s); fm=meta_frame(name,frame)
    Hm=rotAt(PIV[0],PIV[1],(fm['bones'].get('head') or fm['bones'].get('torso'))[2]); HmR=s.roi_M(Hm)
    local=warp(img,np.linalg.inv(HmR),s.w,s.h)
    ys,xs=np.nonzero(s.pa['bun']>0.5); cx,cy=int(xs.mean()),int(ys.max())-10
    ba=hair_front_alpha(s,fm,None,['bun']); br=s.pa['bun']
    fr,(ox,oy)=cropc(local,cx,cy,s); re,_=cropc(s.base_comp,cx,cy,s)
    lay=[(cropc(br>0.5,cx,cy,s)[0],(0,140,0)),(cropc(ba>0.5,cx,cy,s)[0],(220,60,60)),(cropc((ba>0.5)&(br>0.5),cx,cy,s)[0],(220,200,60))]
    g=np.abs(local.astype(np.int16)-s.base_comp).max(-1)
    o=A[name]['c3']
    add(f"{name}  f{frame}  t={fm['t']:.3f}s  bun max offset vs head: geometric {o['geo_max_px']:.2f}px, video {o['vid_max_px']:.2f}px, new bg px at bun/hair seam {o['gap_px_max']}  (head-local)",
        [('video (head-local)',up(fr)),('rest base.png',up(re)),('bun alpha rest/now',up(colmask(lay))),('|video-rest| x4',up(np.repeat(np.clip(cropc(g,cx,cy,s)[0]*4,0,255).astype(np.uint8)[...,None],3,-1)))])
def row_flicker(name,frame):
    s=V(json.load(open(f'{OUT}/data/{name}.json'))['view']); a=grab(vidpath(name),frame-1,s); b=grab(vidpath(name),frame,s)
    st=np.zeros((s.h,s.w),np.uint8)
    for k in s.static: st|=(s.pa[k]>0.5).astype(np.uint8)
    ys,xs=np.nonzero(st); cx,cy=int(xs.min())+30,int(ys.mean())
    d=np.abs(b.astype(np.int16)-a).max(-1); band=cv2.morphologyEx(st,cv2.MORPH_GRADIENT,disk(1))>0
    fa,(ox,oy)=cropc(a,cx,cy,s); fb,_=cropc(b,cx,cy,s)
    dd=np.clip(cropc(d,cx,cy,s)[0]*6,0,255).astype(np.uint8); rgb=np.repeat(dd[...,None],3,-1); rgb[cropc(band,cx,cy,s)[0]&(dd<30)]=(0,60,0)
    add(f"{name}  f{frame-1} (soft, head rotated) -> f{frame} (sharp, head axis-aligned): |diff| x6, static hair outline band in green",
        [(f'f{frame-1} soft',up(fa)),(f'f{frame} sharp',up(fb)),('|f-prev| x6',up(rgb)),('rest base.png',up(cropc(s.base_comp,cx,cy,s)[0]))])
def row_tip(name,strand):
    s=V(json.load(open(f'{OUT}/data/{name}.json'))['view']); o=A[name]['tips'][strand]; frame=o['local_max_frame']
    img=grab(vidpath(name),frame,s); fm=meta_frame(name,frame)
    Hm=rotAt(PIV[0],PIV[1],(fm['bones'].get('head') or fm['bones'].get('torso'))[2]); HmR=s.roi_M(Hm); local=warp(img,np.linalg.inv(HmR),s.w,s.h)
    k,tx,ty=s.tips[strand]; cx,cy=int(tx),int(ty)-20
    keys=[q for q in s.by if q==strand or s.by[q].get('parent')==strand]
    ha=hair_front_alpha(s,fm,None,keys); hr=hair_front_alpha(s,{'hair':{}},None,keys)
    fr,_=cropc(local,cx,cy,s); re,_=cropc(s.base_comp,cx,cy,s)
    lay=[(cropc(hr>0.5,cx,cy,s)[0],(0,140,0)),(cropc(ha>0.5,cx,cy,s)[0],(220,60,60)),(cropc((ha>0.5)&(hr>0.5),cx,cy,s)[0],(220,200,60))]
    add(f"{name}  f{frame}  t={fm['t']:.3f}s  {strand} tip max displacement (head-relative) {o['local_max']:.2f}px geometric / {o['vid_local_max']:.2f}px video-tracked; world {o['world_max']:.2f}px",
        [('video (head-local)',up(fr)),('rest base.png',up(re)),('strand alpha rest/now',up(colmask(lay)))])
def row_wisp(name,frame):
    s=V('tpose'); img=grab(vidpath(name),frame,s); fm=meta_frame(name,frame)
    a=np.array(Image.open(f'{IDLE}/frames/{name}/frames/f{frame:04d}.png'))[s.y0:s.y1,s.x0:s.x1,3]
    r=np.array(Image.open(f'{IDLE}/frames/{name}/rest.png'))[s.y0:s.y1,s.x0:s.x1,3]
    wm=np.array(Image.open(f'{P}/hair/tpose_eye_crossing_wisp_mask.png').convert('L'))[s.y0:s.y1,s.x0:s.x1]>0
    cx,cy=630-s.x0,204-s.y0
    fr,(ox,oy)=cropc(img,cx,cy,s); re,_=cropc(s.base_comp,cx,cy,s)
    hole=(a<255)&(r==255); d=np.zeros(a.shape+(3,),np.uint8); d[hole]=np.stack([255-a[hole]]*3,-1)*4//1 if False else 0
    lay=np.zeros((C,C,3),np.uint8); hc=cropc(hole,cx,cy,s)[0]; ac=cropc(a,cx,cy,s)[0]
    lay[cropc(wm,cx,cy,s)[0]]=(0,90,0); v_=np.clip((255-ac.astype(int))*4,60,255).astype(np.uint8); lay[hc]=np.stack([v_[hc]//3,v_[hc]//3,v_[hc]],-1)
    n=int((hole&(cv2.dilate(wm.astype(np.uint8),disk(2))>0)).sum())
    add(f"PRIORITY tpose wisp  {name} f{frame} t={fm['t']:.3f}s head {fm['bones']['head'][2]:.3f}deg: hair_front wisp (layer 600, sway 0); alpha<255 px at wisp (+2px) = {n}, min alpha {int(a[hole&(cv2.dilate(wm.astype(np.uint8),disk(2))>0)].min()) if n else 255}; nothing opaque underneath",
        [('video frame',up(fr)),('rest base.png',up(re)),('alpha<255 (blue); wisp=green',up(lay)),('lossless render RGB',up(cropc(np.array(Image.open(f'{IDLE}/frames/{name}/frames/f{frame:04d}.png').convert('RGB'))[s.y0:s.y1,s.x0:s.x1],cx,cy,s)[0]))])
# ---- choose rows
row_wisp('tpose',60)
row_wisp('tpose',67)
row_c1('keys_idle_weight_shift_apose',56,note='  [largest bg exposure; outside silhouette = strand swinging off background]')
row_c1('apose',161)
d=A['keys_idle_weight_shift_tpose']['c1']['grey_in']['worst']; row_c1('keys_idle_weight_shift_tpose',d['frame'],note='  [largest bg-inside speck, 2 px blob]')
for n in ['left','right','back']:
    t=max(A[f'keys_idle_weight_shift_{n}']['tips'].items(),key=lambda kv:kv[1]['local_max'])
    fr=t[1]['local_max_frame']; s=V(n); k,tx,ty=s.tips[t[0]]
    row_c1(f'keys_idle_weight_shift_{n}',fr,int(tx),int(ty)-25,note=f'  [ear/nape at max {t[0]} sway]')
row_c2('keys_idle_arm_settle_right',8,'mouth')
row_c2('keys_idle_weight_shift_apose',int(A['keys_idle_weight_shift_apose']['tips']['strand_03']['local_max_frame']),'EyeR')
row_bun('keys_idle_weight_shift_back',A['keys_idle_weight_shift_back']['c3']['geo_max_frame'])
row_flicker('apose',67)
row_flicker('keys_idle_arm_settle_apose',163)
for n in ['apose','apose_hair_middle','apose_hair_stiff']: row_tip(n,'strand_06')
row_tip('keys_idle_weight_shift_apose','strand_06')
# ---- compose
P_=C*Z; pad=8; TH=18
font=ImageFont.load_default()
Wd=4*(P_+pad)+pad; Hd=len(rows)*(P_+TH*3+pad)+pad+60
sheet=Image.new('RGB',(Wd,Hd),(24,24,24)); dr=ImageDraw.Draw(sheet); y=pad
for L in ['Base Hair idle-battle worst frames. Crops 64x64 px at 3x; nothing drawn on her. Panels: video frame | same window of rest base.png on #808080 | masks.','check-1 mask: dark=head/neck mask, purple=closed static silhouette, cyan=new background OUTSIDE silhouette (strand swung off bg: legit),','magenta=new background INSIDE silhouette (hole), white=new near-white, blue=new chroma blue. Strand panels: green=rest, red=now, yellow=overlap.']:
    dr.text((pad,y),L,fill=(255,220,120),font=font); y+=16
y+=8
for title,panels in rows:
    t1,t2=(title[:125],title[125:]) if len(title)>125 else (title,'')
    dr.text((pad,y),t1,fill=(230,230,230),font=font); y+=TH
    if t2: dr.text((pad,y),t2,fill=(230,230,230),font=font)
    y+=TH if t2 else 0
    for j,(lab,im) in enumerate(panels):
        x=pad+j*(P_+pad); dr.text((x,y),lab,fill=(180,180,180),font=font); sheet.paste(Image.fromarray(im),(x,y+TH))
    y+=P_+TH+pad
sheet.save(f'{OUT}/worst_sheet.png'); print('rows',len(rows),sheet.size)
