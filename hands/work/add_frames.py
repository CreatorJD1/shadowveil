import json, shutil, sys, numpy as np
from PIL import Image
ROOT='/workspace/shadowveil'
v=sys.argv[1]; FD=f'{ROOT}/hands/work/frames/{v}'; HD=f'{ROOT}/views/{v}/hands'
rig=json.load(open(f'{HD}/rig.json'))
for p in rig['parts']:
    if not p.get('file') or p['id'].endswith('_palm'): continue
    fr=[f"{p['id']}_f{i}.png" for i in range(3)]
    a=np.array(Image.open(f'{FD}/{fr[0]}')); b=np.array(Image.open(f"{HD}/{p['file']}"))
    assert (a==b).all(), p['id']
    for f in fr: shutil.copy(f'{FD}/{f}',f'{HD}/{f}')
    p['frames']=fr
rig['frameSelect']='contract v1.2: nearest frame by that finger\'s curl, index = floor(curl*2+0.5) -> f0 (rest, identical to "file"), f1, f2. Same canvas, x/y and pivot as the part. Palm has no frames; Thumb1 f1/f2 are copies of f0.'
json.dump(rig,open(f'{HD}/rig.json','w'),indent=1); print('frames added',v)
