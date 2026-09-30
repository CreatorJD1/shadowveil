"""Task 5c: per-frame head-crop sharpness + temporal consistency to pick clean frames near target yaws. Measure only."""
import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
ROOT='/workspace/shadowveil'; F=ROOT+'/reference/apose_turn/frames'; OUT=ROOT+'/hair/qa/export_check'
C=json.load(open(OUT+'/turn_compare.json'))['video']
prev=None; rows=[]
for m in C:
    f=m['f']; im=np.array(Image.open(f'{F}/f{f:03d}.png').convert('L')).astype(np.float32)
    crop=im[30:330,234:534]
    lap=float(ndi.laplace(crop).var())
    d=float(np.abs(crop-prev).mean()) if prev is not None else 0.0; prev=crop
    rows.append(dict(f=f,yaw=m['yaw'],sharp=round(lap,1),dprev=round(d,2)))
s=np.array([r['sharp'] for r in rows]); med=np.median(s)
for r in rows: r['sharp_rel']=round(r['sharp']/med,3)
json.dump(rows,open(OUT+'/turn_clean.json','w'),indent=0)
print('sharp median',med,'min',s.min(),'max',s.max())
low=[r['f'] for r in rows if r['sharp_rel']<0.85]; print('soft frames (<0.85 median):',low)
dp=np.array([r['dprev'] for r in rows[1:]]); print('dprev median',np.median(dp),'spikes',[r['f'] for r in rows[1:] if r['dprev']>3*np.median(dp)])
