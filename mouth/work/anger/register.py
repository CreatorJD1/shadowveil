"""Register the live anger shape (front views only) in views/<v>/mouth/rig.json and mouth/mouth_rig.json. Idempotent."""
import json; import numpy as np; from PIL import Image
ROOT='/workspace/shadowveil'; LIVE=['apose','tpose']
MR=json.load(open(f'{ROOT}/mouth/mouth_rig.json'))
for v in ['apose','tpose','left','right']:
    same=MR['views'].get(v)==json.load(open(f'{ROOT}/views/{v}/mouth/rig.json')); print(v,'mouth_rig mirror identical before:',same)
for v in LIVE:
    p=f'{ROOT}/views/{v}/mouth/rig.json'; r=json.load(open(p))
    k=np.array(Image.open(f'{ROOT}/views/{v}/mouth/anger.png')); yy,xx=np.nonzero(k[...,3])
    r['partsBBox']['anger']=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]
    r['grid']['anger']={'MouthOpen':0.25,'MouthForm':-1}
    r['parts']=[q for q in r['parts'] if q['id']!='mouth_anger']
    pv=r['parts'][0]
    r['parts'].append({'id':'mouth_anger','file':'anger.png','x':0,'y':0,'pivotX':pv['pivotX'],'pivotY':pv['pivotY'],'parent':'base','layer':500})
    json.dump(r,open(p,'w'),indent=2); MR['views'][v]=r
MR['anger']={'views':LIVE,'grid':{'MouthOpen':0.25,'MouthForm':-1},
  'source':'reference/grok_build public/puppet/emotions/anger.png (faces.json kept:anger), cut + uniform scale 0.5 + translate, rotation 0',
  'profiles':'left/right: no side view of the anger face exists -> not registered; nearest pick at (0.25,-1) there is M (tie with OH_half, closed shape wins). Proposal only: mouth/work/anger/proposal/',
  'renderer':'rig/index.html TALK_EXCLUDE should gain "anger" (see mouth/work/anger/summary.md)'}
json.dump(MR,open(f'{ROOT}/mouth/mouth_rig.json','w'),indent=1)
for v in ['apose','tpose','left','right']:
    print(v,'mirror identical after:',MR['views'][v]==json.load(open(f'{ROOT}/views/{v}/mouth/rig.json')))
