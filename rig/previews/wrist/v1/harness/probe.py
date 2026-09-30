# QA probe texture per view: skin-image pixels hidden under the rest hands (the wrist "block"), keyed pure green; QA only, never shown
import json,sys,os,numpy as np
from PIL import Image
V='/workspace/shadowveil/views';OUT='/workspace/shadowveil/rig/previews/wrist/v1/probe'
for v in sys.argv[1].split(','):
    sj=json.load(open(f'{V}/{v}/body/skin.json'));sk=np.array(Image.open(f'{V}/{v}/'+sj.get('image','base_body.png')).convert('RGBA'))
    hj=json.load(open(f'{V}/{v}/hands/rig.json'));hm=np.zeros(sk.shape[:2],bool)
    for p in hj['parts']:
        if p.get('file') and not p.get('hidden'): hm|=np.array(Image.open(f'{V}/{v}/hands/'+p['file']).convert('RGBA'))[...,3]>0
    names=[b['name'] for b in sj['bones']];fa={names.index('forearm_L'),names.index('forearm_R')}
    dom=[max(w,key=lambda q:q[1])[0] for w in sj['weights']];dom=[names.index(d) if isinstance(d,str) else d for d in dom]
    import cv2;fm=np.zeros(sk.shape[:2],np.uint8);Vt=sj['vertices']
    for t in sj['triangles']:
        if any(dom[t[k]] in fa for k in range(3)): cv2.fillPoly(fm,[np.round(np.array([Vt[t[k]] for k in range(3)])).astype(np.int32)],1)
    fm=cv2.dilate(fm,np.ones((3,3),np.uint8))>0
    m=(sk[...,3]>0)&hm&fm;o=np.zeros_like(sk);o[m]=[0,255,0,255]
    Image.fromarray(o).save(f'{OUT}/{v}_probe.png');print(v,'block px under rest hands',int(m.sum()))
