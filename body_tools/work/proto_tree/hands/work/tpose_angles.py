import json,re
d='frames/tpose_v2'; r=json.load(open(d+'/rig.json'))
for p in r['parts']:
    m=re.match(r'^[LR]_(Index|Middle|Ring|Pinky)(\d)$',p['id'])
    if m:
        new=[90,95,15][int(m.group(2))-1]; s=1 if p['maxCurlDeg']>0 else -1
        p['maxCurlDegPrevious']=p['maxCurlDeg']; p['maxCurlDeg']=s*new
r['framesNote']='tpose frames v2: side view, the curl stays in the picture plane and is carried by rotation (maxCurlDeg 90/95/15, previous in maxCurlDegPrevious); f1/f2 replace the square-cut rest pieces with clean rounded segments of the same length and width (her line weight, flat colours, no interior lines); Ring1 frames carry flat skin filling the gap seen through the fist. Thumb keeps rotation only.'
json.dump(r,open(d+'/rig.json','w'),indent=1)
