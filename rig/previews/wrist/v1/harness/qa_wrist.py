# wrist/twist sweep QA: holes (interior alpha<255), block leak (probe green), wrist seam gaps, line-art (width/breaks/kinks) per ROI, per frame
import sys,os,json,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
sys.path.insert(0,os.path.dirname(__file__));from lineart import roi_stats
wd=sys.argv[1];M=json.load(open(wd+'/meta.json'));view=M['view']
ld=lambda p:np.array(Image.open(p).convert('RGBA'))
def holes(a):
    inside=nd.binary_erosion(nd.binary_fill_holes(a>=64),iterations=3);return inside&(a<255)
rest=ld(wd+'/rest.png');RJ=M['restJ']
ROIS=[('wrist','wrist_L'),('wrist','wrist_R'),('elbow','forearm_L'),('elbow','forearm_R'),('armpit','upperArm_L'),('armpit','upperArm_R'),('hip','thigh_L'),('hip','thigh_R'),('knee','shin_L'),('knee','shin_R'),('ankle','foot_L'),('ankle','foot_R')]
# knuckles: rest hand pivots, posed by following the wrist displacement+rotation is not exported -> use a larger wrist ROI (r 70) as the knuckle ROI
visible=lambda k:k in RJ
restS={}
for nm,k in ROIS:
    if visible(k): restS[k]=roi_stats(rest,*RJ[k])
for H in 'LR':
    if 'wrist_'+H in RJ: restS['knuckle_'+H]=roi_stats(rest,*RJ['wrist_'+H],r=80)
z=M['frames'][0];za=ld(f"{wd}/full/000.png")[...,3];zh=holes(za)
def near(mask,J,k,r):
    if k not in J: return 0
    x,y=J[k];h,w=mask.shape;yy,xx=np.ogrid[:h,:w];return int((mask&((xx-x)**2+(yy-y)**2<=r*r)).sum())
hideHands={'left':'R','right':'L'}.get(view)
z0=ld(f"{wd}/full/000.png");zeroS={}
for nm,k in ROIS:
    if k in restS and k in z['J']: zeroS[k]=roi_stats(z0,*z['J'][k])
for H in 'LR':
    if 'knuckle_'+H in restS and 'wrist_'+H in z['J']: zeroS['knuckle_'+H]=roi_stats(z0,*z['J']['wrist_'+H],r=80)
rows=[]
for f in M['frames']:
    im=ld(f"{wd}/full/{f['i']:03d}.png");pr=ld(f"{wd}/probe/{f['i']:03d}.png");a=im[...,3];hm=holes(a)
    g=(pr[...,1]>200)&(pr[...,0]<60)&(pr[...,2]<60)&(pr[...,3]>200)  # stub clearly visible (not the palm's AA edge over it)
    J=f['J'];row=dict(i=f['i'],name=f['name'],holesTotal=int(hm.sum()),holesNew=int(max(0,hm.sum()-zh.sum())),leak={},seam={},line={},fails=[])
    for H in 'LR':
        k='wrist_'+H
        if H==hideHands or k not in J: continue
        row['leak'][H]=near(g,J,k,90);row['seam'][H]=max(0,near(hm,J,k,45)-near(zh,M['frames'][0]['J'],k,45))
        if row['leak'][H]>0: row['fails'].append(f'leak {H} {row["leak"][H]}px')
        if row['seam'][H]>0: row['fails'].append(f'wrist seam gap {H} {row["seam"][H]}px')
    for nm,k in ROIS+[('knuckle','knuckle_L'),('knuckle','knuckle_R')]:
        jk=k.replace('knuckle','wrist');r=80 if nm=='knuckle' else 48
        if k not in restS or restS[k] is None or jk not in J: continue
        if nm in('wrist','knuckle') and k[-1]==hideHands: continue
        s=roi_stats(im,*J[jk],r=r);b=restS[k];b0=zeroS.get(k) or b
        if s is None: continue
        dw=round(s['wmed']-b['wmed'],2);d90=round(s['wp90']-b['wp90'],2);de=s['comps']-b0['comps'];dk=s['kinks']-b0['kinks'];dz=round(b0['wmed']-b['wmed'],2)
        row['line'][k]=dict(dWmed=dw,dWp90=d90,dEnds=de,dKinks=dk,zeroVsRestWmed=dz,zeroVsRestPieces=b0['comps']-b['comps'])
        if abs(dw)>1 or abs(d90)>1.5: row['fails'].append(f'line width {k} {dw:+}/{d90:+}px')
        donor=bool(f.get('twist')) and any(not q.startswith(view+'@') for H in f['twist'] for q in f['twist'][H]['show'])
        if de>=1 and not (donor and nm in('wrist','knuckle')): row['fails'].append(f'line break {k} +{de} piece(s)')
        if dk>max(6,0.25*b0['kinks']) and not (donor and nm in('wrist','knuckle')): row['fails'].append(f'kinks {k} +{dk}')
    row['twist']=f.get('twist');row['issues']=f.get('issues');rows.append(row)
json.dump(dict(view=view,rows=rows,restLine=restS),open(wd+'/qa.json','w'),indent=0)
# sheets: wrist crops per frame (both visible hands), label red on failure
hands=[H for H in 'LR' if H!=hideHands and 'wrist_'+H in RJ]
cs=200;cols=8;n=len(rows);rh=cs+26;sheet=Image.new('RGB',(cols*cs*len(hands),((n+cols-1)//cols)*rh),(40,40,40));dr=ImageDraw.Draw(sheet)
for idx,(f,row) in enumerate(zip(M['frames'],rows)):
    im=Image.open(f"{wd}/full/{f['i']:03d}.png").convert('RGBA');pr=Image.open(f"{wd}/probe/{f['i']:03d}.png").convert('RGBA')
    for hi,H in enumerate(hands):
        x,y=f['J']['wrist_'+H];box=(int(x-85),int(y-60),int(x+85),int(y+110))
        bg=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]),(0,170,170,255));bg.alpha_composite(im.crop(box))
        pa=np.array(pr.crop(box));gm=(pa[...,1]>150)&(pa[...,0]<120)&(pa[...,3]>0);ba=np.array(bg);ba[gm]=[255,0,255,255];bg=Image.fromarray(ba)
        X=(idx%cols)*cs*len(hands)+hi*cs;Y=(idx//cols)*rh;sheet.paste(bg.convert('RGB').resize((cs,cs)),(X,Y+26))
    X=(idx%cols)*cs*len(hands);Y=(idx//cols)*rh;col=(255,80,80) if row['fails'] else (180,255,180)
    dr.text((X+3,Y+2),f"#{row['i']} {row['name']}",fill=col);dr.text((X+3,Y+13),('; '.join(row['fails'])[:70]) or 'ok',fill=col)
sheet.save(os.path.join(os.path.dirname(wd.rstrip('/')),'..','sheets',f'{view}_wrist_sweep.png'))
fails=[r for r in rows if r['fails']];print(view,'frames',n,'failing',len(fails))
for r in fails: print(' #%d %s: %s'%(r['i'],r['name'],'; '.join(r['fails'])))
