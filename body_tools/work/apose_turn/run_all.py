import sys,json,math;sys.path.insert(0,'.')
from measure import *
ours={v:measure(np.array(Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA'))[...,3]>0) for v in ('apose','tpose','left','right','back')}
json.dump(ours,open('ours_measure.json','w'),default=float,indent=1)
raw=json.load(open('raw_span.json'));sp=np.array([r['span_hand']/r['H'] for r in raw]);F=np.arange(1,242)
p1=int(F[40:90][np.argmin(sp[40:90])]);bk=int(F[90:140][np.argmax(sp[90:140])]);p2=int(F[140:190][np.argmin(sp[140:190])])
anch={'front0':1,'profile90':p1,'back180':bk,'profile270':p2,'front360':241}
def solve(s,a,d):   # s = a|cos| + d|sin|, theta in [0,90]
    th=np.radians(np.linspace(0,90,901));v=a*np.cos(th)+d*np.sin(th);return float(np.degrees(th[np.argmin(np.abs(v-s))]))
a0=sp[0];ab=sp[bk-1];d1=sp[p1-1];d2=sp[p2-1]
ang=[]
for i,f in enumerate(F):
    s=sp[i]
    if f<=p1: t=solve(s,a0,d1)
    elif f<=bk: t=180-solve(s,ab,d1)
    elif f<=p2: t=180+solve(s,ab,d2)
    else: t=360-solve(s,(a0+sp[-1])/2,d2)
    ang.append(round(t,1))
rows=[]
for i,f in enumerate(F):
    m=mask_of(f'/workspace/shadowveil/reference/apose_turn/frames/f{f:03d}.png');o=measure(m);t=ang[i]
    prof=abs(((t+90)%180)-90)>60     # near profile
    tgt=(40,1681) if prof else (40,1682)
    n=normalize(o,*tgt)
    # style / quality probes
    a=np.array(Image.open(f'/workspace/shadowveil/reference/apose_turn/frames/f{f:03d}.png').convert('RGB')).astype(int)
    bd=a[...,2]-np.maximum(a[...,0],a[...,1]);mixed=((bd>15)&(bd<=120)).sum();edge=(m&~nd.binary_erosion(m)).sum()
    lab,nc=nd.label(m);sz=sorted(nd.sum(m,lab,range(1,nc+1)),reverse=True)
    skin=m&(a[...,0]>120)&(a[...,0]-a[...,2]>50)
    sk=a[skin];med=np.median(sk,0);dist=np.abs(sk-med).max(1)
    rows.append({'f':f,'t':round(f/24,3),'angle':t,'raw':{k:o[k] for k in o if k not in('arms',)},'arms_raw':o['arms'],'norm':n,
      'q':{'components':int(nc),'comp_sizes':[int(x) for x in sz[:4]],'aa_band_px_per_edge_px':round(mixed/max(edge,1),3),'skin_flat_frac12':round(float((dist<=12).mean()),3),'skin_dark_frac':round(float((sk.sum(1)<med.sum()-60).mean()),3)}})
json.dump({'anchors':anch,'frames':rows},open('turn_measure.json','w'),default=float)
print(anch);[print(r['f'],r['angle'],r['norm']['top'],r['norm']['foot'],r['raw']['H'],r['q']) for r in rows[::10]]
