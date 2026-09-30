import numpy as np, json, pickle, csv
from scipy import ndimage as ndi
R=json.load(open('tmp/pass4.json')); TH=np.array(json.load(open('tmp/theta.json'))['theta']); QA=pickle.load(open('tmp/qa4.pkl','rb'))
N=len(R); vis=[r for r in R if r.get('W')]
front=[r for r in vis if r['idx']<4 or r['idx']>232]
EYE0=float(np.median([r['eyeY'] for r in front])); CHIN0=float(np.median([r['chinY'] for r in front])); SEAM0=float(np.median([r['mouthCy'] for r in front]))
W0=float(np.median([r['W'] for r in front])); CE=CHIN0-EYE0
# ---- refine the angle near front with a face cue: mouth offset from the jaw-contour centre at the seam row
def cue(r): return (r['mouthCx']-(r['faceL']+r['faceR'])/2)/((r['faceR']-r['faceL'])/2)
cal=[(cue(r),np.sin(np.radians(TH[r['idx']]))) for r in vis if 25<=TH[r['idx']]<=50 or 310<=TH[r['idx']]<=335]
k=float(np.sum([c*s for c,s in cal])/np.sum([s*s for c,s in cal]))    # cue = k*sin(theta) (sign included)
theta=TH.copy(); src=['span/keyframe']*N
for r in vis:
    i=r['idx']
    if TH[i]<30 or TH[i]>330:
        s=np.clip(cue(r)/k,-1,1); th=float(np.degrees(np.arcsin(s)))
        if TH[i]>180: th=360+th if th<=0.5 else th
        base=TH[i] if TH[i]<180 else TH[i]; dist=min(base,360-base)          # blend face cue -> span over 10..30 deg
        wgt=np.clip((dist-10)/20,0,1); theta[i]=(1-wgt)*th+wgt*TH[i]; src[i]='face cue' if wgt==0 else 'blend'
# ---- per-frame derived numbers (video px + normalised by chin-to-eye-line CE)
rows=[]; prevm=None
for r in R:
    i=r['idx']; d=dict(frame=r['frame'],theta=round(float(theta[i]),1),angleSource=src[i],visible=bool(r.get('W')))
    if r.get('W'):
        on=r['leftOnContour'] or r['rightOnContour']
        eye=r['eyeY'] if (r.get('irises') and len(r['irises'])==2) else EYE0
        chin=r['chinY'] if r.get('chinY') else CHIN0
        ce=chin-eye
        if on:   # profile: lift = seam height at the lip front minus the back-corner height
            yf,yb=(r['yL'],r['yR']) if r['leftOnContour'] else (r['yR'],r['yL']); lift=yf-yb
        else: lift=r['lift']
        # morph / smear: change of the mouth mask vs the previous frame (centre-aligned IoU) and W jump vs 5-frame median
        m=QA[i][0][...,1]==255
        d.update(W_px=r['W'],H_px=r['H'],W_over_CE=round(r['W']/ce,3),W_over_frontW=round(r['W']/W0,3),
                 cornerLift_px=round(lift,2),cornerLift_over_CE=round(lift/ce,3),
                 bothCornersVisible=(not on),contourSide=('left' if r['leftOnContour'] else 'right' if r['rightOnContour'] else ''),
                 mouthCx=r['mouthCx'],seamY=r['mouthCy'],eyeLineY=round(eye,2),eyeSource=('irises' if eye!=EYE0 else 'front median'),chinY=chin,CE_px=round(ce,2),
                 noseX=r['noseX'],noseY=r['noseY'],
                 seam_below_eye_over_CE=round((r['mouthCy']-eye)/ce,3),chin_below_seam_over_CE=round((chin-r['mouthCy'])/ce,3),
                 seam_below_nose_over_CE=(round((r['mouthCy']-r['noseY'])/ce,3) if r.get('noseY') else None),
                 mouth_dx_from_nose_over_CE=(round((r['mouthCx']-r['noseX'])/ce,3) if r.get('noseX') else None),
                 faceL=r['faceL'],faceR=r['faceR'],mouth_pos_in_jaw=round((r['mouthCx']-r['faceL'])/(r['faceR']-r['faceL']),3),
                 closed=bool(r['openSpan']<1.5 and r['teethPx']<3),openSpan_px=r['openSpan'],teeth_px=r['teethPx'],sharp=r['sharp'])
    rows.append(d)
# midline: in near-front frames the nostril centroid is the midline; relative offset of the mouth centre from it
Wv=np.array([d.get('W_px',np.nan) for d in rows]); med=ndi.median_filter(np.nan_to_num(Wv,nan=0),5)
for j,d in enumerate(rows):
    if d['visible']:
        d['W_jump_px']=round(float(Wv[j]-med[j]),2)
        d['crisp']= 'crisp' if d['sharp']>=15.5 and abs(d['W_jump_px'])<1.5 else ('soft' if d['sharp']>=13 else 'smeared')
json.dump(dict(EYE0=EYE0,CHIN0=CHIN0,SEAM0=SEAM0,CE=CE,W0=W0,k=k,rows=rows),open('turn_stats.json','w'),indent=1)
with open('turn_mouth_frames.csv','w',newline='') as f:
    keys=[]; [keys.append(k_) for d in rows for k_ in d if k_ not in keys]
    w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
print('EYE0 %.2f CHIN0 %.1f SEAM0 %.2f CE %.2f W0 %.2f k %.3f'%(EYE0,CHIN0,SEAM0,CE,W0,k))
for d in rows:
    if d['visible'] and (int(d['frame'][1:])-1)%4==0:
        print(d['frame'],d['theta'],d['angleSource'][:4],'W',d['W_px'],'W/CE',d['W_over_CE'],'lift',d['cornerLift_px'],'both',d['bothCornersVisible'],'closed',d['closed'],'sharp',d['sharp'],d['crisp'],'jump',d['W_jump_px'],'dxNose/CE',d['mouth_dx_from_nose_over_CE'],'seam-nose',d['seam_below_nose_over_CE'],'chin-seam',d['chin_below_seam_over_CE'],'posJaw',d['mouth_pos_in_jaw'])
