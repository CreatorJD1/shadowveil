# mkback.py <name> I M R P  : L seg1 lean deg per finger (seg2 = 2/3, seg3 = 1/2), R mirrored
import json,sys,os
n=sys.argv[1];L=dict(zip(['Index','Middle','Ring','Pinky'],map(float,sys.argv[2:6])))
j=json.load(open('data_backup/back_rig.json'))
for p in j['parts']:
    for f,v in L.items():
        for s,k in ((1,1),(2,2/3),(3,0.5)):
            if p['id'] in (f'L_{f}{s}',f'R_{f}{s}'):
                x=round(v*k,2)*(1 if p['id'][0]=='L' else -1);p['maxCurlDeg']=int(x) if x==int(x) else x
os.makedirs(f'scratch/back_{n}',exist_ok=True);json.dump(j,open(f'scratch/back_{n}/rig.json','w'),indent=1)
