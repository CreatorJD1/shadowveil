"""Task 5b: per-frame yaw estimate, hair silhouette metrics on video frames vs our 5 views (same metric code). Measure only."""
import numpy as np, json, math
from PIL import Image
from scipy import ndimage as ndi
ROOT='/workspace/shadowveil'; F=ROOT+'/reference/apose_turn/frames'; OUT=ROOT+'/hair/qa/export_check'
M=json.load(open(OUT+'/turn_measure.json')); W={r['f']:r['waistW'] for r in M}
# yaw keys from waist-width extrema: f001 front(0), f061 profile(90, her left side, face screen-left), f109 back(180), f161 profile(270), settle ~f229 (360)
K=[(1,0),(61,90),(109,180),(161,270),(229,360)]
def yaw(f):
    if f>=229: return 360.0
    for (a,A),(b,B) in zip(K,K[1:]):
        if a<=f<=b:
            wa,wb=W[a],W[b]; wmin=min(wa,wb); wmax=max(wa,wb); c=np.clip((W[f]-wmin)/(wmax-wmin),0,1)
            ang=math.degrees(math.acos(c))  # 0 at the wide key, 90 at the narrow key
            return A+ (ang if wa>wb else 90-ang)
def metrics(rgb,fg,hairmask=None):
    r,g,b=[rgb[...,k].astype(int) for k in range(3)]
    ys,xs=np.nonzero(fg); top,bot=ys.min(),ys.max(); Hf=bot-top
    dark=fg&(np.maximum(np.maximum(r,g),b)<75) if hairmask is None else hairmask
    lab,n=ndi.label(ndi.binary_dilation(dark,iterations=2)&fg)
    # hair component = the one containing the topmost dark pixels
    reg=lab[top:top+int(0.25*Hf)]; cnt=np.bincount(reg.ravel()); cnt[0]=0; big=int(cnt.argmax())
    hc=(lab==big)&dark
    hy,hx=np.nonzero(hc)
    skin=fg&(r>95)&(r-b>25)&(r>=g)&~hc
    head=(hc|skin); rows=range(top,top+int(0.2*Hf))
    wr=np.array([(lambda q:(q.max()-q.min()+1) if len(q) else 0)(np.nonzero(head[y])[0]) for y in rows])
    sw=np.percentile(wr[wr>0],95); k=0
    while k<len(wr) and wr[k]<0.62*sw: k+=1
    by,bx=np.nonzero(head[top:top+max(k,1)]); sy,sx=np.nonzero(head[top+k:top+k+70])
    scx=sx.mean()
    # skull extents
    return dict(figH=int(Hf),skullW=round(float(sw),1),bun_vis_h=round(k/Hf,4),bun_dx=round((bx.mean()-scx)/sw,3),
                hair_top=round((hy.min()-top)/Hf,4),hair_low=round((hy.max()-top)/Hf,4),hair_h_over_skullW=round((hy.max()-hy.min())/sw,2),
                hair_px_over_fig2=round(len(hy)/Hf**2*1e4,2))
out={'video':[],'ours':{}}
for f in range(1,242):
    im=np.array(Image.open(f'{F}/f{f:03d}.png').convert('RGB')); r,g,b=[im[...,k].astype(int) for k in range(3)]
    fg=~((b>140)&(r<90)&(g<90)&(b-np.maximum(r,g)>90))
    m=metrics(im,fg); m.update(f=f,yaw=round(yaw(f),1)); out['video'].append(m)
for v in ['apose','tpose','left','right','back']:
    im=np.array(Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA')); fg=im[...,3]>128
    u=np.zeros(fg.shape,bool)
    import glob
    for p in glob.glob(f'{ROOT}/views/{v}/hair/*.png'): u|=np.array(Image.open(p))[...,3]>128
    m=metrics(im[...,:3],fg); m2=metrics(im[...,:3],fg,hairmask=u&fg)
    out['ours'][v]=dict(dark_threshold=m,hair_parts=m2)
json.dump(out,open(OUT+'/turn_compare.json','w'),indent=0)
for v,m in out['ours'].items(): print(v,m['hair_parts'])
for m in out['video'][::6]: print(m)
